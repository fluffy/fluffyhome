
function doUpdate( ) 
{
    $('#category').hide();
    
    cat =  $('#category select').val();
    
    if ( cat === 'Group' )
    {
        $('#category').hide();
        $('#indicatorGroup').hide();
        $('#calcGroup').hide();
    }

    if ( cat === 'Sensor' )
    {
        $('#category').hide();
        $('#calcGroup').show();
        
        val =  $('#units select').val();
        
        switch(val) 
        {
        case 'C':
        case '%':
        case 'F':
            $('#type').hide();
            $('#groupTotal').hide();
            $('#indicatorGroup').show();
            break;
        case 'W':
            $('#type').show();
            $('#groupTotal').show();
            $('#indicatorGroup').hide();
            break;
        case 'lps':
            $('#type').show();
            $('#groupTotal').show();
            $('#indicatorGroup').hide();
            break;
        default:
            $('#type').hide();
            $('#groupTotal').hide();
            $('#indicatorGroup').hide();
            break;
        };
    }
};


$(document).ready(function() 
{
    doUpdate();
    $('#category select').change( function() { doUpdate(); } );
    $('#units select').change( function() { doUpdate(); } );
});


