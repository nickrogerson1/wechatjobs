const checkBox = document.querySelector('#select-all-items')
const checkboxes = document.querySelectorAll('.checkbox')

const applyToAll = () => checkboxes.forEach(x => checkBox.checked && !x.disabled ? x.checked = true : x.checked = false)

// Turn it on and off when all or some selected
const turnMainOnOff = () => {
    const allChecked = [...checkboxes].every(x => x.checked)
    allChecked ? checkBox.checked = true : checkBox.checked = false
}

// Only add listeners when there are submissions
if(checkBox){
    checkboxes.forEach(x => x.addEventListener('click', turnMainOnOff))
    checkBox.addEventListener('click', applyToAll)
}
const formFrozen = document.querySelector('#undo-form-freeze')
if (formFrozen) formFrozen.addEventListener('click', undoFormFreeze)

// Make sure to re-enable checkboxes before submission or they won't go through
const deleteFiles = document.querySelector('#delete-files')
if(deleteFiles) deleteFiles.addEventListener('submit', () => checkboxes.forEach(x => x.disabled = false))

const dropdown = document.querySelector('#dropdown')
if(dropdown) dropdown.addEventListener('change', processCheckboxes)



function processCheckboxes() {

    let index = dropdown.selectedIndex
    console.log(`Selected Index: ${index}`)

    // Continue checking otherwise
    const checkboxes = document.querySelectorAll('.checkbox')
    const trs = document.querySelectorAll('tbody tr')
    const ids = [...checkboxes].reduce((a,x) => {
        if(x.checked){
            a = a + x.id + '/'
            }
            return a
    },'')


    // Check and warn them if they've selected nothing
    // Providing it's not the 1st option
    if(index && !ids.length) {
        const warningText = "You've not selected anything! Please select at least one job and try again."
        return showWarningAlert(warningText)
    }
    



    // Delete button
    if(dropdown.value == 'Delete'){
    // Display delete confirmation and fade out form
    // Complicated way of checking for one due to split
        if(ids.split('/').filter(x => x).length === 1){
            console.log('Fired!!!!!')
            const h4 = document.querySelector('#delete-area h4')
            const deleteButton = document.querySelector('#delete')
            let text = 'Are you sure you want to delete the selected '
            // Modify text depending on page
            if(location.pathname === '/job-applications/'){
                text += 'job application?'
            } else if(location.pathname === '/view-applications/'){
                text += 'candidate?'
            } else {
                text += 'job?'
            }
            
            h4.innerHTML = text
            deleteButton.innerHTML = 'YES, DELETE IT!'
            formFrozen.innerHTML = 'NO, KEEP IT!'
        }
        
        document.querySelector('#delete-area').style.cssText = `
            display: block;
            visibility: visible;`
        dropdown.disabled = true
        checkBox.disabled = true
        
// Got through rows and apply CSS when selected for deletion
        trs.forEach( tr => {
            tr = tr.children
            tr[0].children[0].disabled = true

            if(tr[0].children[0].checked){
                for(let i = 1; i < tr.length; i++)
                    tr[i].style.cssText = `
                    text-decoration:line-through;
                    opacity:0.5;
                    pointer-events: none;`
            }
        })
    } 


    // Applications Update
    // 1) Check for table errors
    // 2) If none, update table
    // 3) Send Ajax and update DB
    
        
        
    // CANDIDATES
    // Candidates can do 2 bulk actions + delete:  Re-apply or Revoke an Application
    if (['Re-apply', 'Revoke'].includes(dropdown.value)){

        const action = dropdown.value == 'Re-apply' ? 'pending' : 'revoked'

        // Check for form errors
        for(let i = 0; i < trs.length; i++){

            const cb = $(trs[i]).find('.checkbox')[0]

            if(cb.checked){
            // Get the value of this row's status
                const statusVal = $($(trs[i]).find('.pxp-company-dashboard-job-status span')).text().trim()

            // Check for Re-apply errors
                if(action === 'pending'){

                    if('Rejected' === statusVal){ 
                        const warningText = "You can't re-apply for applications that have rejected you. Delete them if you no longer need them."
                        return showWarningAlert(warningText)
                    }

                    if('Pending' === statusVal){
                        const warningText = "You can't re-apply for applications that you have already applied for."
                        return showWarningAlert(warningText)
                    }

            // Check for Revoke errors
                } else {

                    if('Rejected' === statusVal){ 

                        const warningText = "You can't revoke applications that have rejected you. Delete them instead."
                        return showWarningAlert(warningText)
                    }
        
                    if('Revoked' === statusVal){
                        const warningText = "You can't apply for applications that you have already revoked!"
                        return showWarningAlert(warningText)
                    }
                }
            }
        }

        
        // All good, then process them
        // Reset form th checkbox at the same time
        $('th')[0].children[0].checked = false

        let checked = ''

        trs.forEach(r => {
        
            const cb = $(r).find('.checkbox')[0]

            if (cb.checked){

                const statusSpan = $(r).find('.pxp-company-dashboard-job-status span')

            // Actions for Re-apply
                if (action === 'pending'){

                    statusSpan.removeClass(['bg-success','bg-danger','bg-warning'])
                    .addClass('bg-secondary').html('Pending')
                    $(r).find('.fa-check')
                        .removeClass('fa-check').addClass('fa-ban')
                        .parent().attr('title', 'Revoke')
                    
            // Actions for Revoke
                } else {

                    statusSpan.removeClass(['bg-success','bg-danger','bg-secondary'])
                    .addClass('bg-warning').html('Revoked')
                    $(r).find('.fa-ban')
                        .removeClass('fa-ban').addClass('fa-check')
                        .parent().attr('title', 'Re-apply')
                }

                cb.checked = false
                const pk = $(r).data('appPk')
                // console.log(pk)
                checked ? checked += ',' + pk : checked += pk

            }
        })

        // Send off to the server
        sendAjaxRequest(JSON.stringify(checked), action)
    }





    // EMPLOYERS
    // Employers can do 3 bulk actions + delete: Reset, Approve and Reject an Application
    if (['Reset','Approve','Reject'].includes(dropdown.value)){
        
        let action; 
        if(dropdown.value == 'Reset'){
            action = 'pending'
        } else if (dropdown.value == 'Approve'){
            action = 'approved'
        } else {
            action = 'rejected'
        }

        // Check for errors
        for(let i = 0; i < trs.length; i++){

            const cb = $(trs[i]).find('.checkbox')[0]

            if(cb.checked){
            // Get the value of this row's status
                const statusSpan = $($(trs[i]).find('.pxp-company-dashboard-job-status span')).text().trim()

            // Check for errors
            // Reject all attempts to edit a Revoked app
                if('Revoked' === statusSpan){
                    const warningText = "You can't edit applications that have been revoked by the candidate."
                    return showWarningAlert(warningText)   

                }   else if(action === 'pending'){

                    if('Pending' === statusSpan){ 
                        const warningText = "You can't reset applications that are Pending."
                        return showWarningAlert(warningText)
                    }

                } else if(action === 'approved'){

                    if('Approved' === statusSpan){
                        const warningText = "You can't approve applications again."
                        return showWarningAlert(warningText)
                    }

                } else {

                    if('Rejected' === statusSpan){
                        const warningText = "You can't reject applications again."
                        return showWarningAlert(warningText)
                    }
                }
            }
        }



        // All good, then process them
        // Reset form th checkbox at the same time
        $('th')[0].children[0].checked = false

        let checked = ''

        trs.forEach(r => {
        
            const cb = $(r).find('.checkbox')[0]
        // Only execute on checked boxes, otherwise ignore
            if (cb.checked){

                const statusSpan = $(r).find('.pxp-company-dashboard-job-status span')

            // Pending
                if (action === 'pending'){

                    statusSpan.removeClass(['bg-success','bg-danger','bg-secondary'])
                    .addClass('bg-secondary').html('Pending')
                    
            // Approved
                } else if(action === 'approved'){

                    statusSpan.removeClass(['bg-success','bg-danger','bg-secondary'])
                    .addClass('bg-success').html('Approved')
                    
            // Rejected
                } else {

                    statusSpan.removeClass(['bg-success','bg-danger','bg-secondary'])
                    .addClass('bg-danger').html('Rejected')
                }

            //Reset icons
                 $(r).find('.icons').removeAttr('disabled')
                 $(r).find(`.${action}`).attr('disabled', '')

                cb.checked = false
                const pk = $(r).data('appPk')
                // console.log(pk)
                checked ? checked += ',' + pk : checked += pk

            }
        })

        // Send off to the server
        sendAjaxRequest(JSON.stringify(checked), action)

    }


    // Reset dropdown
    dropdown.selectedIndex = 0
}






function sendAjaxRequest(pks, status){

    console.log(typeof pks)

    $.ajax({
        type: 'POST',
        url: '/update-app-status/',
        data: {
            csrfmiddlewaretoken, pks, status
        },
        dataType: 'json',
    });
}



function undoFormFreeze(){
    document.querySelector('#delete-area').style.cssText = `
                display: none;
                visibility: hidden;`
    dropdown.selectedIndex = 0
    dropdown.disabled = false
    checkBox.disabled = false
    checkboxes.forEach(x => x.disabled = false)
    document.querySelectorAll('tr td:not(:first-child)')
        .forEach(x => x.style.cssText = `
                text-decoration:initial;
                opacity:1;
            `)
}


// Warn them when they don't select anything
$(document).ready(function() {
    $("#error-alert").hide()

// Fire when redirected from job post
    if($('#custom-alert')){
        $('#custom-alert').fadeTo(5000, 500).slideUp(500)
    }

// Handle promoted ads
    $('.promoted-ad').each(function() {
        const duration = $(this).data().time
    
    // Don't set up timer if already expired
        if(duration < 0){
            return $(this).removeClass('bg-primary')
                .addClass('bg-danger')
                .text('Promotion Expired')
        }
        startTimer(duration, $(this));
    })


})


// Function for ALL alerts
function showWarningAlert(warningText){
    document.body.scrollTop = document.documentElement.scrollTop = 80;
    dropdown.selectedIndex = 0
    $("#error-alert").html(warningText)
    .fadeTo(3000, 500).slideUp(500)
}

// Works when messages sent from server
if($('.subs-removed-success')){
    $(".subs-removed-success").fadeTo(5000, 500).slideUp(500);
}



function startTimer(timer, el) {
    let days, hours, minutes, seconds;
    const addZero = v => v < 10 ? '0' + v : v;
    
    const interval = setInterval(function () {

        days = addZero(parseInt(timer / (60 * 60 * 24)));
        hours = addZero(parseInt(timer / (60 * 60) % 24));
        minutes = addZero(parseInt(timer / 60 % 60));
        seconds = addZero(parseInt(timer % 60));

        el.text(`Promoted ${days}:${hours}:${minutes}:${seconds}`);
        
        if (timer-- <= 0) {
            clearInterval(interval)
            el.removeClass('bg-primary')
                .addClass('bg-danger')
                .text('Promotion Expired')
        }
    }, 1000);
}



$('.delete-single-job').on('click', function(){
    if($(this).data().promoted){
    //Add the form details so it can be submitted as normal
        $('#removed-promoted').attr('form', `job-${$(this).data().jobPk}`)
        $('#delete-warning').modal('show');
    } else {
    //No warning, just delete it
        $(`#job-${$(this).data().jobPk}`).submit()    
    }
})

