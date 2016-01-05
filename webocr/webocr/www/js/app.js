(function() {
    var model = {
        services: []
    }

    var controller = {
        init: function () {
            this.intervalID = setInterval(this.refreshServiceList, 5000);
            this.refreshServiceList()
            this.url = $('#url');
            this.tag = $('#tag');
            this.ports = $('#ports');

            var host = 'ws://localhost:1234/websocket';
            var websocket = new WebSocket(host);
            websocket.onopen = function (evt) {
            };
            websocket.onmessage = function(evt) {
                websocketLogView.addMessage(evt.data);
            };
            websocket.onerror = function (evt) {
            };

            tableView.init();
            createServiceView.init();
        },

        refreshServiceList: function() {
            console.log('refreshing service list');
            $.get('http://localhost:1234/api/v1/services', function(data,status,req){
                model.services = data.services;
                tableView.render();
            }).fail(function() {
                websocketLogView.addMessage("Unable to get services");
            })
        },

        addService: function() {
            imageView.loadImage($("#url").val());
            alertView.hideAll();
            $("#addBtn").prop("disabled", true);
            $("#websocketsLog").val('');
            $.post('http://localhost:1234/api/v1/services',
                    JSON.stringify({
                        url: $("#url").val(),
                        tag: $("#tag").val(),
                        ports: $("#ports").val()
                    }), controller.onCreated)
                    .fail(controller.onFail);
        },

        onCreated: function(data,textStatus,req) {
            console.log('post success!')
            var loc = req.getResponseHeader('Content-Location');
            controller.pollForCompletion(loc);
        },
        onSuccess: function(xhr, textStatus, errorThrown) {
           alertView.displaySuccess();
           $("#addBtn").prop("disabled", false);
           tableView.render()

        },
        onFail: function() {
            alertView.displayError();
            $("#addBtn").prop("disabled", false);
            tableView.render()
        },
        pollForCompletion: function(location) {
            var done = false;
            $.get(location, function(data,status,request){
                console.log('polling ', location);
                console.log(data);
                // if redirected, do not reschedule func, check state (SUCCESS or FAILED)
                // else if getting 200 with the status ...
                if (data.state != 'SUCCESS' && data.state != 'FAILED') {
                    websocketLogView.addMessage("Pending ...\n");
                    setTimeout(function() {
                        controller.pollForCompletion(location);
                    },1000);
                } else if (data.state == 'SUCCESS'){
                    $("#resultTxt").val(data.celery_state.result);
                    controller.onSuccess();
                } else if (data.state == 'FAILED') {
                    controller.onFail();
                }
            }).fail(controller.onFail);
        },
        getServices: function() {
            return model.services;
        }
    }

    var tableView = {
        init: function() {
        },
        render: function() {
            var services = controller.getServices();
            $("#servicesTbl").empty();
            for(var i=0;i<services.length;i++) {
                var tr="<tr>";
                var td1="<td>"+services[i]["url"]+"</td>";
                var td4="<td>"+services[i]["state"]+"</td>";
                var td5="<td>"+services[i]["result"]+"</td></tr>";
                $("#servicesTbl").append(tr+td1+td4+td5);
            }
        }

    }

    var createServiceView = {
        init: function(){
            $('#addBtn').click(controller.addService);
        }
    }

    var logView = {
        addMessage: function(msg) {
            $('#log').append(msg);
        }
    }

    var websocketLogView = {
        addMessage: function(msg) {
            $('#websocketsLog').val($('#websocketsLog').val() + msg);
        }
    }

    var alertView = {
        displaySuccess: function() {
            $("#deploy-ok-alert").show()
        },
        displayError: function() {
            $("#deploy-error-alert").show()
        },
        hideAll: function() {
            $("#deploy-ok-error").hide()
            $("#deploy-ok-alert").hide()
        }
    }

    var imageView = {
        loadImage: function(url) {
            // delete all image if any
            $('#ocrImg').remove();
            // Load new image
            var img = new Image();
            $(img).load(function(){
                $('#ocrImgDiv').append($(this));
            }).attr({
                id: "ocrImg",
                src: url
            }).error(function(){
              //do something if image cannot load
            });
        }
    }
    controller.init();
})();