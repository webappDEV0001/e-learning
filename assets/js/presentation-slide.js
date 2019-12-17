


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

	$("#start-exam-pre").on('click', function () {
				var id = $(".current").attr('id');
				if(id != TOTAL_SLIDES ){
                    next_slide_id = parseInt(id)+1;
                    if(next_slide_id == TOTAL_SLIDES ){
                        $("#start-exam-pre").css('visibility','hidden');
                        $("#go_back").css('display','block');
                    }
                    $("#previous_slide_pre").css('visibility','visible');
                    $("#"+id).removeClass("current");
                    $("#"+next_slide_id).addClass("current");
                    $("#seen_slide").text(next_slide_id);
                }

		});

	$("#previous_slide_pre").on('click', function () {
				$("#go_back").css('display','none');
				var id = $(".current").attr('id');
				if(id != 1 ){
                    prev_slide_id = parseInt(id)-1;
                    if(prev_slide_id == 1){
                        $("#previous_slide_pre").css('visibility','hidden');
                    }
                    $("#start-exam-pre").css('visibility','visible');
                    $("#"+id).removeClass("current");
                    $("#"+prev_slide_id).addClass("current");
                    $("#seen_slide").text(prev_slide_id);
                }

		});



document.onkeydown = checkKey;

function checkKey(e) {

    e = e || window.event;
    event.preventDefault();
    check_current_slide = $(".current").attr('id');
    if (e.keyCode == '37' && check_current_slide!=1 ) {
    	$("#previous_slide_pre").click();
    }

    else if (e.keyCode == '39' && check_current_slide != TOTAL_SLIDES ) {
    	$("#start-exam-pre").click();
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

check_current_slide = $(".current").attr('id');
if (check_current_slide == TOTAL_SLIDES){
    $("#start-exam-pre").css("visibility","hidden");
}


