// Hacky way to not add the q to the location
$(document).on("submit", "form", e => {
    // e.preventDefault()
  console.log(e)
  v = e.target;
    for(let i = 0; i < v.length; i++){
        v[i].disabled = v[i].value === '';
    }
})

$('.like-button').on('click', function() {
    const pk = $(this).parent().parent().parent().data('pk')

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
    const pks = JSON.stringify($(this).parent().data('pk').toString())
    let status
  
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

    $.ajax({
        type: 'POST',
        url: 'https://wechatjobs.com/update-app-status/',
        data: {
            csrfmiddlewaretoken, pks, status, 
            jobPk: true
        },
        dataType: 'json',
    });
})

$('.reselect').on('change', function() {
        location = this.value
})


const teaching_jobs = ['high school', 'international school', 'middle school', 'online teacher', 'online teaching', 'primary school',
        'private school', 'public school', 'secondary school', 'teaching', 'training center', 'training centre', 'university'
]


$('#id_type').on('change', function(){

    if(teaching_jobs.includes(this.value)){
        $('#subject-container').removeClass('d-none')
    } else {
        $('#subject-container').addClass('d-none')
        $('#subject-container option[value="0"]').prop('selected',true);
    }
})


document.querySelector('#search-form').addEventListener('formdata', e => {
    //Get rid of show_all if more than one - otherwise '?' will show on its own
    if([...e.formData.keys()].length > 1 && e.formData.get('options') === 'show_all'){
        e.formData.delete('options');
    }
});


function autocomplete(inp, arr, input) {
  /*the autocomplete function takes two arguments,
  the text field element and an array of possible autocompleted values:*/
  var currentFocus;
  /*execute a function when someone writes in the text field:*/
  inp.addEventListener("input", function(e) {
      var a, b, i, val = this.value;
      /*close any already open lists of autocompleted values*/
      closeAllLists();
      if (!val) { return false;}
      currentFocus = -1;
      /*create a DIV element that will contain the items (values):*/
      a = document.createElement("DIV");
      a.setAttribute("id", this.id + "autocomplete-list");
      a.setAttribute("class", "autocomplete-items");
      /*append the DIV element as a child of the autocomplete container:*/
      this.parentNode.appendChild(a);
      /*for each item in the array...*/
      for (i = 0; i < arr.length; i++) {
        /*check if the item starts with the same letters as the text field value:*/
        if (arr[i][0].substr(0, val.length).toUpperCase() == val.toUpperCase()) {
          /*create a DIV element for each matching element:*/
          b = document.createElement("DIV");
          /*make the matching letters bold:*/
          b.innerHTML = "<strong>" + arr[i][0].substr(0, val.length) + "</strong>";
          b.innerHTML += arr[i][0].substr(val.length);
          /*insert a input field that will hold the current array item's value:*/
          b.innerHTML += "<input type='hidden' value='" + arr[i][0] + "' data-id='" + arr[i][1] + "'>";
          /*execute a function when someone clicks on the item value (DIV element):*/
              b.addEventListener("click", function(e) {
              /*insert the value for the autocomplete text field:*/
              inp.value = this.getElementsByTagName("input")[0].value;
              
              input.value = this.getElementsByTagName("input")[0].dataset['id']
              /*close the list of autocompleted values,
              (or any other open lists of autocompleted values:*/
              closeAllLists();
          });
          a.appendChild(b);
        }
    }
});
  /*execute a function presses a key on the keyboard:*/
inp.addEventListener("keydown", function(e) {
    // Reset the value to be sent every time they type
    input.value = ''
      var x = document.getElementById(this.id + "autocomplete-list");
      if (x) x = x.getElementsByTagName("div");
      if (e.keyCode == 40) {
        /*If the arrow DOWN key is pressed,
        increase the currentFocus variable:*/
        currentFocus++;
        /*and and make the current item more visible:*/
        addActive(x);
      } else if (e.keyCode == 38) { //up
        /*If the arrow UP key is pressed,
        decrease the currentFocus variable:*/
        currentFocus--;
        /*and and make the current item more visible:*/
        addActive(x);
      } else if (e.keyCode == 13) {
        /*If the ENTER key is pressed, prevent the form from being submitted,*/
        e.preventDefault();
        if (currentFocus > -1) {
          /*and simulate a click on the "active" item:*/
          if (x) x[currentFocus].click();
        }
    }
});

function addActive(x) {
    /*a function to classify an item as "active":*/
    if (!x || !x.length) return false;
    /*start by removing the "active" class on all items:*/
    removeActive(x);
    if (currentFocus >= x.length) currentFocus = 0;
    if (currentFocus < 0) currentFocus = (x.length - 1);
    /*add class "autocomplete-active":*/
    x[currentFocus].classList.add("autocomplete-active");
}

function removeActive(x) {
    /*a function to remove the "active" class from all autocomplete items:*/
    for (var i = 0; i < x.length; i++) {
      x[i].classList.remove("autocomplete-active");
    }
}

function closeAllLists(elmnt) {
    /*close all autocomplete lists in the document,
    except the one passed as an argument:*/
    var x = document.getElementsByClassName("autocomplete-items");
    for (var i = 0; i < x.length; i++) {
      if (elmnt != x[i] && elmnt != inp) {
      x[i].parentNode.removeChild(x[i]);
    }
  }
}
/*execute a function when someone clicks in the document:*/
document.addEventListener("click", function (e) {
    closeAllLists(e.target);
});
}

const wxidInput = document.querySelector('#wxid')
const groupInput = document.querySelector('#group')

autocomplete(document.getElementById("wxid-input"), posters, wxidInput);
autocomplete(document.getElementById("group-input"), groups, groupInput);

$('.toggle input').click(() => {
    $('#advanced-options').slideToggle('2000');
});