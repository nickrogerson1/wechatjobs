<h1 align="center">WeChatJobs – a Chinese job-aggregator app</h1>

### About This Project
On WeChat, you will find tonnes of groups which can hold up to 500 members each. Some of these groups focus on posting different job opportunities aimed at foreigners in China, mostly to do with English teaching and modelling/acting.

These group chats are great but if you happen to be a member of 10 or 20, or even 10000, then it becomes difficult to keep track of who is posting what and can become quickly overwhelming.

This app aims to solve this particular problem and is able to process hundreds, possibly thousands, of messages per second and decipher whether it’s just a random message or an actual job. 
It uses Celery to distribute work across multiple threads and Redis as a lighting fast in-memory cache to check for duplicates (most of which are). The results of this process can then be accessed via the website.

### Tech Stack
This app was built with Python, the Django Web Framework and PostgreSQL. JQuery and Bootstrap were also used for frontend development. Celery and Redis were used to handle incoming messages and update the database.
The trickiest part of this build was the image and video handling. The Python Pillow package was used to resize and reformat images on the server. Filepond and Cropper.js were used to upload and edit images and videos on the frontend while Nanogallery was used to display the uploaded image and videos.

### Key Features
-	Candidates can favourite and apply to jobs easily on the site.
-	Employers can add jobs to and promote them easily on the site.
-	Users can easily add CVs, images and videos to the site with Filepond which are then saved to an S3 bucket.
-	Incoming potential jobs are parsed and handled with Redis and Celery almost instantaneously.
-	Search feature allows users to search all jobs based on any number of criteria ie. location, job type or any arbitrary term.
-	Users can easily contact the admin via a contact form and AmazonSES.

### Future Improvements
- Use AI to parse jobs and decipher whether it’s an actual job or just a random message.
- Add a user dashboard.
- Add FFMPEG to zip and reformat videos server side. 

### Current Status
The app is currently frozen due to high server costs and issues with the third party WeChat API provider.

### Miscellaneous
I had to do another initial commit post launch to wipe some historical password leaks. This project was never intended to be a public repo, so was never an issue.
