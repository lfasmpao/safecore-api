$("#yourSelector").live("click", function(){
        var id = parseInt($(this).val(), 10);
        if($(this).is(":checked")) {
            // checkbox is checked -> do something
        } else {
            // checkbox is not checked -> do something different
        }
});