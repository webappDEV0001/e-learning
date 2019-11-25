$(function() {

	var time_counter = undefined;

	function getCookie(name) {
		var cookieValue = null;
		if (document.cookie && document.cookie !== '') {
			var cookies = document.cookie.split(';');
			for (var i = 0; i < cookies.length; i++) {
				var cookie = cookies[i].trim();
				// Does this cookie string begin with the name we want?
				if (cookie.substring(0, name.length + 1) === (name + '=')) {
					cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
					break;
				}
			}
		}
		return cookieValue;
	}


	function makeTimer(end_time) {

		var endTime = Date.parse(new Date(end_time));
		var now = Date.parse(new Date(new Date().toUTCString().substr(0, 25)))

		timeLeft = (endTime - now) / 1000;
		console.log('test tes test ' + timeLeft);
		if (timeLeft < 0) {
			manageUserSession("GET");
			return "";
		}

		var days = Math.floor(timeLeft / 86400); 
		var hours = Math.floor((timeLeft - (days * 86400)) / 3600);
		var minutes = Math.floor((timeLeft - (days * 86400) - (hours * 3600 )) / 60);
		var seconds = Math.floor((timeLeft - (days * 86400) - (hours * 3600) - (minutes * 60)));

		// if (minutes < "10") { minutes = "0" + minutes; }
		// if (seconds < "10") { seconds = "0" + seconds; }

		return "Time left: " + minutes + " minutes " + seconds + " seconds";
	}

	function slideSeen() {
		let csrftoken = getCookie('csrftoken');
		$.ajax({
			type: 'PUT',
			url: $("#exam-screen").data('url'),
			data: { 'slide': 'seen' },
			beforeSend: function (xhr, settings) {
				$('div.loading').show();
				xhr.setRequestHeader("X-CSRFToken", csrftoken);
			},
			success: function(data)
			{
				manageUserSession("GET");
			},
			error: function(xhr, data)
			{
				console.log(data);
			},
			complete: function () {
				$('div.loading').hide();
			}
		});
	}

	function sendAnswer(id, q_id, phase) {
		let csrftoken = getCookie('csrftoken');
		$.ajax({
			type: 'PUT',
			url: $("#exam-screen").data('url'),
			data: {
				'answer': id,
				'question': q_id,
				'phase': $("#question-box").data('phase')
			},
			beforeSend: function (xhr, settings) {
				$('div.loading').show();
				xhr.setRequestHeader("X-CSRFToken", csrftoken);
			},
			success: function(data)
			{
				$("#question-box").append(data.content)
				if ('explanation' in data) {
					$("#explanation").removeClass('d-none');
					$("#explanation-text").html(data.explanation);
					$("#next-question").on('click', function () {
						manageUserSession("GET");
					});
				}
			},
			error: function(xhr, data)
			{
				console.log(data);
			},
			complete: function () {
				$('div.loading').hide();
			}
		});
	}

	function manageUserSession(type) {

		let csrftoken = getCookie('csrftoken');
		let rtnData = undefined;
		let url_container = $("#exam-screen").data('url');
		$.ajax({
			type: type,
			url: url_container,
			beforeSend: function (xhr, settings) {
				$('div.loading').show();
				xhr.setRequestHeader("X-CSRFToken", csrftoken);
			},
			success: function(data)
			{
				$("#exam-screen").html(data.content);

				if (data.state == 'init') {

					$("#start-exam").on('click', function(e) {
						rtnData = manageUserSession("PATCH"); // start exam
					});

				} else if (data.state == 'start') {

					manageUserSession("GET"); // get actual session state

				} else if (data.state == 'question') {

					if (data.session.stop_time) {
						$("#timer").html(makeTimer(data.session.stop_time));
						clearInterval(time_counter);
						time_counter = setInterval(function() { $("#timer").html(makeTimer(data.session.stop_time)); }, 1000);
					}

					$("#phase-text").html($("#question-box").data('phase'));
					$(".answer-btn").on('click', function(e) {
						sendAnswer($(e.target).data('pk'), $(e.target).data('qpk'))
					});

				} else if (data.state == 'end' || data.state == 'no_time_left') {

					clearInterval(time_counter);
					$("#check-results").on('click', function (e) {
						var location = '/exam/scores/' + data.session.id;
						window.location = location;
					});

				} else if (data.state == 'slide') {

					$(".next-slide").on('click', function () {
						slideSeen();
					});
				}
			},
			error: function(xhr, data)
			{
				console.log(data);
			},
			complete: function () {
				$('div.loading').hide();
			}
		});
	}

	manageUserSession("GET"); // get user session

});
