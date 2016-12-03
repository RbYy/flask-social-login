$(document).ready(function() {

    var firstLevelLength = $(".level-1").length;
    var angleBetween = 360 / firstLevelLength;
    var angle = angleBetween/2 - angleBetween
        $(".level-1").each(function(index){
            angle += angleBetween;
            $(this).css("transform", "rotate(-" + angle + "deg)")
            $(".btn-icon", this).css("opacity", "0")
        });

    function getLevelDepth(){
        var levels = 0;
        $(".rotater").each(function(){
            thisLevel = $(this).attr("id").split('-')[0]
            levels = thisLevel > levels ? thisLevel : levels
        });
        return levels;
    }

    $(".trigger").click(function() {
        $(".btn").removeClass("active");
        $(".menu").toggleClass("active");
        var angleBetween = 360 / firstLevelLength;
        var angle = angleBetween / 2 - angleBetween
        if ($(".menu").attr('class').indexOf('active') >= 0){
            $(".level-1 .btn").each(function(index){
                angle += angleBetween;
                $(this).css({transform: "translateX(10em) rotate(" + angle + "deg)", opacity: "1"})
            });
        }else{
            $(".rotater .btn").each(function(index){
                $(this).css({transform: "", opacity: "0"})
            });                     
        }
    });

    $(".rotater").click(function() {
            var id = $(this).attr("id")
            var level = id.charAt(0)
            var children = $("." + id);
            var childrenBtns = $("." + id + " .btn")
            var angleBetween = 26 - level * 6
            var levelUp = Number(level) + 1

        if($(this).attr('class').indexOf('active') >= 0){
            $(this).removeClass('active');
            $(".level-" + levelUp).removeClass("active");
            for (var i = levelUp; i <= getLevelDepth(); i++) {
                $(".level-" + i + " .btn").each(function(index){
                    $(this).css({transform: "", opacity: "0"})
                });
            }           
        }else {
            $(".level-" + level).removeClass("active");
            $(".level-" + levelUp).removeClass("active");
            for (var i = levelUp; i <= getLevelDepth(); i++) {
                $(".level-" + i + " .btn").each(function(index){
                    $(this).css({transform: "", opacity: "0"})
                });
            }
            $( this).addClass('active')
            originalAngle = $(this).attr('style').split(/[()d]+/).filter(function(e) { return e; })[1];
            angle = originalAngle - children.length * angleBetween / 2 + angleBetween / 2     
            children.each(function(index){
                $(this).css("transform", "rotate(" + angle + "deg)")
                angle += angleBetween 
            })
            angle = originalAngle - children.length * angleBetween / 2 + angleBetween / 2 
            childrenBtns.each(function(index){     
                $(this).css({
                    transform: "translateX(" + Number(10+level*6) + "em) rotate(" + angle * -1 + "deg)",
                    "translate-origin": "0% 0%",
                    opacity: "1"
                });
                angle += angleBetween;
            });            
        }
    });

    $(".checkable").click(function(e) {
     e.stopPropagation()
     $(this).toggleClass("checked");
     // primer kako lahko v javascriptu uporabiš rezultate
     var result = ''
     $(".checked").each(function(index){
        result += "<p><i class='" + $('i', this).attr('class') + "'></i></p>";
        });
     $(".results").html(result);
    });   
});