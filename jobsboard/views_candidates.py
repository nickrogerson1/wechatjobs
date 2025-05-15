from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import FormView, ListView, DeleteView
from django.views import View
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.contrib import messages
from django.template.loader import render_to_string

from .models import *
from .forms import *
from .views import MediaMixin
from .tasks import *
from django.core.mail import send_mail

import sys
import json
from datetime import date

from django_drf_filepond.models import TemporaryUpload


# Makes sure they are logged in as a Candidate
class UserHasPermission(LoginRequiredMixin,UserPassesTestMixin):

    permission_denied_message = 'You need to be a Candidate to view this!'
    user_type = 'candidate'

    def test_func(self):
        return hasattr(self.request.user, self.user_type)





# Shared with employer when viewing application profiles
class CandidateProfile(LoginRequiredMixin, View):

    model = SiteUser
    template_name = 'jobsboard/candidates/candidate-profile.html'

    def get(self, request, *args, **kwargs):

        if 'pk' in self.kwargs:
            pk = self.kwargs['pk']

        # Get all job applications for this employer
        # and find jobs with applications from this candidate
        # and status not revoked
        # Only allow access if the candidate has an active application
            if hasattr(request.user, 'employer'):
                if not JobApplication.objects.filter(job__employer=request.user.employer, candidate__user__pk=pk).exclude(status='revoked'):
                    raise PermissionDenied
            else:
        # Deny candidates
                raise PermissionDenied

        else:
            pk = request.user.id

        print(f"PK: {pk}")

        c = self.model.objects.select_related('candidate').prefetch_related('candidate__images', 'candidate__videos').get(id=pk)
        # print(c.__dict__)


        cxt = {
            'profile_pic_url': c.profile_pic.url if c.profile_pic else None,
            'name': c.first_name,
            'email': c.email,
            'sex' : c.candidate.sex,
            'wechat_id': c.wechat_id,
            'phone_number': c.phone_number,
            'city': c.city,
            'country': c.country,
            'age': self.calculate_age(c.candidate.dob) if c.candidate.dob else None,
            'intro': c.intro,
            'job_types': c.job_types,
            'cv': c.candidate.cv,
            'cv_fname': os.path.basename(c.candidate.cv.name),
            'cover_letter': c.candidate.cover_letter,
            'images': c.candidate.images.all,
            'videos': c.candidate.videos.all
        }

        return render(request, self.template_name, context=cxt)
    

    def calculate_age(self, dob):
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
   





# Stop this updating if image or video still being uploaded
class EditCandidateProfile(UserHasPermission,FormView):
    model = SiteUser
    form_class = CandidateForm
    template_name = 'jobsboard/candidates/edit-candidate-profile.html'
    user_type = 'candidate'

    # Need to set the object before it gets the form kwargs
    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(self.model, id=self.request.user.id)
        return super().dispatch(request, *args, **kwargs)
    

    def get(self, request, *args, **kwargs):
        
        if self.request.user.candidate.cv:
            self.extra_context = {
                'cv_url': self.request.user.candidate.cv.url,
                'cv_fname' : self.request.user.candidate.cv_fname
            }

        print(f'KWARGS: {kwargs}')
        return super(EditCandidateProfile, self).get(self, request, *args, **kwargs)


    def post(self, request, *args, **kwargs):
        
        u = self.user
        form = self.get_form()


        print(f'HAS CHANGED: {form.changed_data}')
        print(request.POST)

        cv_changed = int(request.POST.get('cv_changed'))
        print(f'CV CHANGED: {cv_changed}')

        if not form.has_changed() and not cv_changed:
            print('NOT changed fired!')
            messages.info(request, "Your profile was NOT updated as you didn't change anything.")
            # return self.form_invalid(form)
            return self.get(self, request, *args, **kwargs)


        if form.is_valid():
            print('FORM VALID!')

            u.intro = form.cleaned_data['intro']
            u.wechat_id = form.cleaned_data['wechat_id']
            u.phone_number = form.cleaned_data['phone_number']
            u.city = form.cleaned_data['city']
            u.country = form.cleaned_data['country']
            u.job_types = form.cleaned_data['job_types']
            u.save()


            u.candidate.sex = form.cleaned_data['sex']
            u.candidate.dob = form.cleaned_data['dob']

            file = request.FILES.get('cv')

            if file:
                u.candidate.cv = file
            
            u.candidate.save()

            request.user = u
           
            messages.success(request, 'Your profile has been successfully updated.')
            return self.get(self, request, *args, **kwargs)
        else:
            print('FORM INVALID!')
            print(form.errors)

            if self.request.user.candidate.cv:
                self.extra_context = {
                    'cv_url': self.request.user.candidate.cv.url,
                    'cv_fname' : self.request.user.candidate.cv_fname
                }

            messages.error(request, 'Your profile was not updated! Please review the errors.')
            return self.form_invalid(form)


    # def get_form_kwargs(self):
    #     """ Passes the request object to the form class."""
    #     kwargs = super(EditCandidateProfile, self).get_form_kwargs()
    #     kwargs['request'] = self.request
    #     return kwargs
    
    def get_form_kwargs(self):
        """ Passes the user to the form class and sets initial data. """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user

    # Ensure initial form data is set to the current data of the instance
    # Makes sure that form changes are detected properly
        initial_data = {
            'sex': 'M' if self.user.candidate.sex else 'F',
            'dob': self.user.candidate.dob,
            # 'cv': self.user.candidate.cv,
            'intro': self.user.intro,
            'wechat_id': self.user.wechat_id,
            'phone_number': self.user.phone_number,
            'city': self.user.city,
            'country': self.user.country,
            'job_types': self.user.job_types
        }
        kwargs['initial'] = initial_data
        return kwargs

    




class EditCandidateMedia(UserHasPermission,View,MediaMixin):
    model = Candidate
    template_name = 'jobsboard/candidates/edit-candidate-media.html'

    MAX_VIDEOS_ALLOWED = 10
    MAX_IMAGES_ALLOWED = 20

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    # Handle POST request
    def post(self, request):

        # The delay before local files are removed
        countdown = 0
       
        data = request.POST
        # print(f'DATA: {data}')
        
        profile_pic = data.getlist('profile')
        images = data.getlist('images')
        videos = data.getlist('videos')
        thumbnails = data.getlist('thumbnails')

        stored_uploads = {} #possibly now redundant
        upload_ids = []
        

        if len(profile_pic[0]):
            print(f'PROFILE PIC: {profile_pic}')
        # Can only be one profile pic at any one time
            upload_id = profile_pic[0]
            tu = TemporaryUpload.objects.get(upload_id=upload_id)
            fname, ftype = tu.upload_name.split('.')
            fpath = f'profile-pics/{upload_id}-{fname}.webp'
            webp_image = self.create_webp_image(tu, fpath, True)
            del tu
        
        # No need to store uploads here as there is no gallery to update
            # stored_uploads[upload_id] = [fname, loc]

            try:
                user = SiteUser.objects.get(id=request.user.id)
                print(f'USER: {user}')
                user.profile_pic.delete()
                user.profile_pic = webp_image
                user.save()
                upload_ids.append(upload_id)
            except Exception as e:
                print(e)
            finally:
                webp_image.close()
                countdown += 10


        if len(images[0]):

        # Server side check they haven't bypassed the JS
            images_uploaded_count = CandidateImage.objects.filter(candidate=request.user.candidate).count()
            print(f'TOTAL IMAGES: {images_uploaded_count}')

            if images_uploaded_count > self.MAX_IMAGES_ALLOWED:
                return JsonResponse({
                    'success': False,
                    'reason': 'You have exceeded the maximum number of images you can upload.'
                })

            for upload_id in images:
                tu = TemporaryUpload.objects.get(upload_id=upload_id)
                from django.utils import timezone
                print(f'SINCE UPLOAD TIME: {timezone.now() - tu.uploaded}')
                if (timezone.now() - tu.uploaded) < timezone.timedelta(hours=1):
                    print('Its less than an hour')
                

                fname, ftype = tu.upload_name.split('.')
                fpath = f'images/{upload_id}-{fname}.webp'

                webp_image = self.create_webp_image(tu, fpath)
                del tu

                kwargs = {
                    'candidate': Candidate.objects.get(user=request.user),
                    'image': webp_image
                }

                try:
                    image = CandidateImage.objects.create(**kwargs)
                    stored_uploads[upload_id] = [fpath, image.id]
                    upload_ids.append(upload_id)
                except Exception as e:
                    print(e)
                finally:
                    webp_image.close()
                    countdown += 20


        if len(videos[0]):

        # Server side check they haven't bypassed the JS
            videos_uploaded_count = CandidateVideo.objects.filter(candidate=request.user.candidate).count()
            print(f'TOTAL VIDS: {videos_uploaded_count}')

            if videos_uploaded_count > self.MAX_VIDEOS_ALLOWED:
                return JsonResponse({
                    'success': False,
                    'reason': 'You have exceeded the maximum number of videos you can upload.'
                })

            for vid_thumb in thumbnails:

                video_id, thumb = next(iter(json.loads(vid_thumb).items()))

                print(f'VIDEO: {video_id}')
                # print(f'THUMB: {thumb}')

                # with open(Path(__file__).with_name('ten_hag.mp4'),'rb') as f:
                # process = (
                #     ffmpeg
                #     # .input(Path(__file__).with_name('ten_hag.mp4'), format='mp4')
                #     .input('pipe:', format='mp4', movflags='faststart')
                #     .output('pipe:', format='webm')
                #     # , preset='fast'
                #     # .overwrite_output()
                #     # .run_async(pipe_stdin=False, pipe_stdout=True)
                #     .run(capture_stdout=True, input=f)
                # )

                # with open(tu.file.file, 'rb') as f:
                #     process = (
                #         ffmpeg
                #         .input(f, ss='00:00:05')
                #         .output('pipe:', format='webp', vframes=1)
                #         .overwrite_output()
                #         .run_async(pipe_stdout=True)


                tu = TemporaryUpload.objects.get(upload_id=video_id)
                print(tu.__dict__)

            # Temporary server side validation of video files in case client side fails
                valid_extensions = ('mp4', 'webm')
                ext = tu.upload_name.split('.')[-1]

                if ext not in valid_extensions:
                    self.delete_temp_files(stored_uploads)
                    raise PermissionDenied

                fpath = f'videos/{video_id}-{tu.upload_name}'
               
                file = InMemoryUploadedFile(tu.file, 'FileField',fpath, ext,sys.getsizeof(tu), None)
                # Clear temp upload 
                del tu

                # storage_module_name = settings.DJANGO_DRF_FILEPOND_STORAGES_BACKEND
                # storage_backend = _get_storage_backend(storage_module_name)

                # try:
                #     storage_backend.save(fpath, tu.file)
                #     file = StoredUpload(upload_id=tu.upload_id,
                #                     file=fpath,
                #                     uploaded=tu.uploaded,
                #                     uploaded_by=tu.uploaded_by)
                #     file.save()
                # except Exception as e:
                #     raise e
                # from django_drf_filepond.api import store_upload

                # su = store_upload(video_id, fpath)


                kwargs = {
                    'candidate': Candidate.objects.get(user=request.user),
                    'video': file,
                    'thumbnail': thumb
                }

                try:
                    video = CandidateVideo.objects.create(**kwargs)
                    # video_id != video.id
                    stored_uploads[video_id] = [fpath, video.id]
                    upload_ids.append(video_id)
                    print(f'video_id: {video_id}')
                    print(f'fpath: {fpath}')
                    print(f'video.id: {video.id}')
                except Exception as e:
                    print(f'ERROR: {e}')
                finally:
                    file.close()
                    countdown += 20


        # Delete temp uploads once everything has finished
        # print(f'STORED UPLOADS: {stored_uploads}')
        print(f'UPLOAD IDS: {upload_ids}')
        print(f'TYPE: {type(upload_ids)}')
        print(f'COUNTDOWN: {countdown}')
        delete_temp_files.apply_async(args=upload_ids, countdown=countdown)

        # Return the list of uploads that were stored.
        return HttpResponse(json.dumps({'status': 'OK',
                            'uploads': stored_uploads}),
                            content_type='application/json')




class DeleteMedia(UserHasPermission,DeleteView):

     # Need to check he owns this file before deleting
    def remove_objs(self, model, objs):
        for pk in objs:
            try:
                # print(f'USER ID: {self.request.user.id}')
                # THIS NEEDS TESTING WITH ANOTHER USER!!!! 
                obj = model.objects.get(candidate=self.request.user.candidate,pk=pk)
                # print(f'{"IMG" if model == CandidateImage else "VIDEO" }: {obj}')
                obj.image.delete(save=False) if model == CandidateImage else obj.video.delete(save=False)
                obj.delete()
            except model.DoesNotExist:
                print('No media found for that user or with that PK!')
    

    def delete(self, request, *args, **kwargs):

        if 'img' in request.GET:
            images = request.GET.getlist('img')
            # print(images)
            self.remove_objs(CandidateImage, images)

        if 'video' in request.GET:
            videos = request.GET.getlist('video')
            # print(videos)
            self.remove_objs(CandidateVideo, videos)
            
        return JsonResponse({'success': True}, status = 200)
    



class DeleteCV(UserHasPermission,DeleteView):
    
    def delete(self, request, *args, **kwargs):

        try:
            candidate = Candidate.objects.get(pk=request.user.candidate.pk)
            print(f'CV: {candidate.cv}')
            candidate.cv.delete()
            return JsonResponse({'success': True}, status = 200)
        except Candidate.DoesNotExist:
            print('Candidate does not exist!')



# Display all liked jobs
class FavouriteJobs(UserHasPermission,ListView):
    model = FavouriteJob
    template_name = 'jobsboard/candidates/favourite-jobs.html'
    context_object_name = 'jobs'
    paginate_by = 10

    def get_queryset(self):
        if self.request.GET.get('order') == 'A':
            order = ''
            self.extra_context = {'order': 'A'}
        else: 
            order = '-'
        return self.model.objects.filter(candidate=self.request.user.candidate).order_by(f'{order}job__time_created')


# Display all jobs applied for
class JobApplications(UserHasPermission,ListView):
    model = JobApplication
    template_name = 'jobsboard/candidates/job-apps.html'
    context_object_name = 'jobs'
    paginate_by = 10

    def get_queryset(self):
        if self.request.GET.get('order') == 'A':
            order = ''
            self.extra_context = {'order': 'A'}
        else: 
            order = '-'
        return self.model.objects.select_related('job__employer__user').filter(candidate=self.request.user.candidate, candidate_removed=False).order_by(f'{order}time_created')




# Handles the deletion and creation of ALL favourites/likes
class CreateDeleteLike(UserHasPermission,View):
    model = FavouriteJob

    def post(self, request, *args, **kwargs):

        # Delete here if coming from Favourites page
        if request.POST.getlist('bulk-delete'):

            # print(request.POST.getlist('pks'))

            pks = [int(x) for x in request.POST.getlist('pks')]
            print(pks)

            try:
                # Uses JobApplication model
                self.model.objects.filter(pk__in=pks, candidate__pk=request.user.candidate.pk).delete()
                g = ' was' if len(pks) == 1 else 's were'
                messages.success(request, f'Your selected favourite{g} successfully removed.')
                return redirect(reverse('fav-jobs'))
            except Exception as e:
                print(e)
                messages.error(request, 'Operation failed!')
                return redirect(reverse('fav-jobs'))

        else:
            # Delete and add one by one elsewhere
            # Favourites can only be added one by one
            pk = json.loads(request.POST.get('pk'))

            try:
                # Goes through Job model
                self.model.objects.get(candidate=self.request.user.candidate, job__pk=pk).delete()
                return JsonResponse({'success': True})

            except self.model.DoesNotExist:
                try:
                    job = Job.objects.get(pk=pk)
                    self.model.objects.create(candidate=self.request.user.candidate, job=job)
                    return JsonResponse({'success': True})
                except Exception as e:
                    print(e)
                    return JsonResponse({'success': False})

            except Exception as e:
                print(e)
                return JsonResponse({'success': False})
           




class GetWechatID(UserHasPermission,View):

    def post(self, request, *args, **kwargs):

        pk = request.POST.get('pk')
        # print(f'PK: {pk}')

        try:
            job = Job.objects.get(pk=pk)
            print(f'JOB: {job}')
            
        except Job.DoesNotExist:
            print("Job doesn't exist")
            return JsonResponse({'failed': True}, status = 200)
    

        if job.wxid_alias:
            job.wxid_alias.wx_alias_request_by_user = request.user.candidate
            print('ALIAS REQUESTED!')
            job.wxid_alias.save()

        message = render_to_string('admin_emails/wechat_request.html', {
            'username': request.user.username,
            'user_ip': self.get_client_ip(request),
            'name': request.user.first_name,
            'email': request.user.email,
            'country': request.user.get_country_display(),
            'time_created': job.time_created,
            'message_group_from': job.group.group_name if job.group else 'N/A',
            'poster_handle': job.wx_handle.handle if job.wx_handle else 'N/A',
            'job_description': job.job_description
        })

        send_mail(
            'Wechat User ID requested',
            message,
            '"WechatJobs" <mail@wechatjobs.com>',
            ['nickrogerson11@gmail.com'],
            html_message = message
        )
        return JsonResponse({'success': True}, status = 200)
    

    def get_client_ip(self,request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

