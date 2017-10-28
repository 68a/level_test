function loading(){

    var startDateTime = new Date().getTime();
    
    setInterval(function(){
        var now = new Date().getTime();
        var distance = now - startDateTime; 
        var seconds = Math.floor((distance % (1000 * 60)) / 1000);
        $("#loading_text").html("正在生成试卷..."+ seconds);
    },1000);
    
    $("#loading").show();
    $("#content").hide();
}
