$(document).ready(function()
{
$(".settings").click(function()
{
var X=$(this).attr('id');
if(X==1)
{
$(".submenu").hide();
$(this).attr('id', '0'); 
}
else
{
$(".submenu").show();
$(this).attr('id', '1');
}
});
$(".submenu").mouseup(function()
{
return false
});
$(".settings").mouseup(function()
{
return false
});
$(document).mouseup(function()
{
$(".submenu").hide();
$(".settings").attr('id', '');
});
});