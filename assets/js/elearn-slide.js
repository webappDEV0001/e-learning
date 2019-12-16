function GoOutFullscreen() {
	if(document.exitFullscreen)
		document.exitFullscreen();
	else if(document.mozCancelFullScreen)
		document.mozCancelFullScreen();
	else if(document.webkitExitFullscreen)
		document.webkitExitFullscreen();
	else if(document.msExitFullscreen)
		document.msExitFullscreen();
}


function GoInFullscreen(elem) {
	  elem = elem || document.documentElement;
		if (elem.requestFullscreen) {
		  elem.requestFullscreen();
		} else if (elem.msRequestFullscreen) {
		  elem.msRequestFullscreen();
		} else if (elem.mozRequestFullScreen) {
		  elem.mozRequestFullScreen();
		} else if (elem.webkitRequestFullscreen) {
		  elem.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
		}

}

function GoOutFullscreen(elem)  {
		if (document.exitFullscreen) {
		  document.exitFullscreen();
		} else if (document.msExitFullscreen) {
		  document.msExitFullscreen();
		} else if (document.mozCancelFullScreen) {
		  document.mozCancelFullScreen();
		} else if (document.webkitExitFullscreen) {
		  document.webkitExitFullscreen();
		}
}

var device;

if(window.matchMedia("(max-width: 767px)").matches){
           device="mobile";
    } else{
            device="desktop";
}

$("#full-screen").click(function(){
	      check =$(".ppt_info_slide").hasClass("full_screen");
	      if(check == true){
	      	  	$(".ppt_info_slide").removeClass("full_screen");
	      	  GoOutFullscreen();
	      	   $("#full-screen").attr('data-original-title', 'View full Screen');
	      	    $("#full-screen").attr('title', 'View full Screen');
	      }
	      else{
	      	  $(".ppt_info_slide").addClass("full_screen");
	      	  GoInFullscreen();
	      	   $("#full-screen").attr('data-original-title', 'Exit full Screen');
	      	   $("#full-screen").attr('title', 'Exit full Screen');

    		}

});

var counter=0;

document.onkeydown = checkKey;

function checkKey(e) {

    e = e || window.event;
    event.preventDefault();
    check = $("#1").hasClass("current");

    if (e.keyCode == '37' && check == false) {
       $(".previous-slide").click();
    }
    else if (e.keyCode == '39') {
       $(".next-slide").click();
    }
    else if (e.keyCode == '38') {
        // up arrow
        $("#full-screen").click();
    }
    else if (e.keyCode == '40') {
        // down arrow
        $("#full-screen").click();
    }

}
$("#"+SEEN_SLIDES).addClass("current");
if(SEEN_SLIDES == 1){
	$(".previous-slide").css('display','none');
}

if ($(window).width() < 700)
{
	window.setTimeout(function () {
    $(".alert-success").fadeTo(500, 0).slideUp(500, function () {
        $(this).remove();
    });
}, 5000);
}
