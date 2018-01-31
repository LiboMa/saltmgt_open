    function delete_env(dev_id, project_id ){
    
        var url="./mgdeployenv/"+dev_id+"/delete/";
        /*var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();*/
    
        $("#delModal").modal('show');
        $("#confirmed").on('click',function(){
        
        var jqxhr = $.post(url,{'project_id':project_id,'md_deploy_env_id':dev_id, 'csrfmiddlewaretoken': csrftoken}, function(){
                
        })
        .done(function(){
                window.location.reload();
            })
        .fail(function(data) {
                console.log(data.name);
                alert("Backend Error");
              });
        });
    }


