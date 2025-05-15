$('.like-button').on('click', function() {
    const pk = $(this).data('pk')
    console.log(pk)
    $.ajax({
        type: 'POST',
        url: 'https://wechatjobs.com/handle-likes/',
        data: {
            csrfmiddlewaretoken, pk
        },
        dataType: 'json',
    });
})


$('.apply-btn').on('click', function() {
    let status;
    $('.apply-btn').each(function() {

        if(this.className.includes('applied')){
            $(this).removeClass('applied')
            .addClass('bg-warning')
            .html('Re-apply')
            status = 'revoked'
        } else {
            $(this).removeClass('bg-warning')
            .addClass('applied')
            .html('Revoke App')
            status = 'pending'
        }
    })


    $.ajax({
        type: 'POST',
        url: 'https://wechatjobs.com/update-app-status/',
        data: {
            csrfmiddlewaretoken, 
            status,
            pks: JSON.stringify(jobPk),
            jobPk: true
        },
        dataType: 'json',
    });
})

$(document).ready(function() {
    $('#custom-alert').hide()
})

const copyText = async e => {
    try {
        //Stop link from firing
        e.preventDefault()
        await navigator.clipboard.writeText(location.href)
        document.body.scrollTop = document.documentElement.scrollTop = 0;
        $("#custom-alert").fadeTo(3000, 500).slideUp(500)
    } catch (e){
        console.log(e)
    }
}

$('#copy-link').on('click', copyText)

$('#request-wechat').on('click', function(){

    $(this).parent().parent()
        .replaceWith( `<div class="col-6 mt-1 pxp-single-job-category">
            <div class="pxp-single-job-category-icon" style="background-color: var(--pxpMainColorLight); opacity:0.5;">
            <span style="color:black;" class="fa fa-wechat"></span></div>
            <div class="pxp-single-job-category-label">
            <h5 style="opacity:0.5; color:black;">Wechat ID Requested</h5>
            </div>
            </div>`)

    const { pk } = $(this)[0].dataset

    console.log(`PK: ${pk}`)

    $.ajax({
            type: 'POST',
            url: 'https://wechatjobs.com/get-wechat-id/',
            data: {csrfmiddlewaretoken, pk},
            dataType: 'json',
    });
})