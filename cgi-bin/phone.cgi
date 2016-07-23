#!/usr/bin/perl -w

#my $html_dir    = "../html"; #Home use
my $html_dir = "/path/to/web";

my $phone_dir = "$html_dir/projects/phone";
my $pics_dir    = "$phone_dir/pics";
my $com_dir     = "$phone_dir/comments";

my $img_link    = "/projects/phone/pics";

my $cgi_script  = "/cgi-bin/phone.cgi";

my $ns_vdir     = "/noodlespeak";

my $MAX_ENTRY_DISPLAY = 5;

my $total_entries=0;

#==============================================================================
sub generate_AN_logo {
print <<AN_LOGO;
<br><br>
<div align=right>
<table cellspacing=0 cellpadding=0 width=400>
<tr><td>
 <a href=/index.html target="_top">
   <img src=/projects/phone/icons/an-dblue.gif 
        width=215 height=38 border=0 align=right>
 </a>
</td><td width=40>&nbsp;<td></tr><tr><td>
<div align=right>
<b><font face="Verdana"><font color="#FFFFFF"><font size=-2>
Photographer of boring things</font></font></font></b>
</div></td></tr></table></div>
AN_LOGO
}
#==============================================================================
sub generate_top {

print <<END_OF_TOP;
Content-type: text/html;

<!doctype html public "-//w3c//dtd html 4.0 transitional//en">
<html>
<head>

   <link rel="stylesheet" href="/projects/phone/tmobo.css" type="text/css">

   <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
   <meta name="Author" content="AngryNoodle">
   <title>Angry Noodle's Roving T-mobile Cam</title>
</head>
<body text="#000000" bgcolor="#AFAFD8" link="#0000EE" vlink="#551A8B" alink="#FF0000">

END_OF_TOP

generate_AN_logo();
}


#==============================================================================
sub dump_starting_at {
  
  my $index = shift(@_);
  my @allfiles;
  my $total_entries;
  my $req_index;

 
  opendir(PDIR, "$pics_dir") or die "Couldn't get Directory\n";
  @allfiles = grep  { /.jpg/ && !/~/ } readdir PDIR;
  closedir PDIR;

  @allfiles = sort @allfiles;

  foreach (@allfiles){
      print "==> $_<br>\n";
  }

  $total_entries = scalar(@allfiles);
  #print "Total entries: $total_entries<br>\n";

  #Start at the end if no input
  if(($index<0) || ($index>=$total_entries)){
     $index=$total_entries-1;
  }
  $req_index = $index; #copy original

  print "<center>\n";

  $count = $MAX_ENTRY_DISPLAY;
  while (($count > 0) && ($index >= 0) && ($index <= $total_entries)){
    my $tmp   = @allfiles[$index];
    my $mtime = (stat("$pics_dir/$tmp"))[9];

    print "<img src=$img_link/$tmp border=2><br>\n";
    print "<table><tr><td>\n";
    print "<span class=\"pdate\">";
    #print "<b><font face=Verdana><font color=#000055><font size=-2>";
    printf "Posted: %s \n", scalar localtime $mtime;
    print "</td><td width=30> </td>\n";

    my $num_comments;
    my $base_name = $tmp;
    $base_name =~ s/.jpg//;
    
    if ( -e "$com_dir/$base_name.txt"){
         #grep on comment tag.. is there a faster way?
         $num_comments=0;
         open(F, "<$com_dir/$base_name.txt");
         while(<F>){
              $num_comments=$num_comments+1 if( /AN_COMMENT_TAG/ );
         }
         close(F);
    } else {
       $num_comments = 0;
    }
    


    print "<td>"; 
    #print "$tmp $base_name "; #Add file name
    #print "<a href=/cgi-bin/phone-comment.cgi?entry=$base_name>";
    print "<a href=/cgi-bin/phone-comment.cgi?entry=$index>";
    print "Comments ($num_comments)</a>";
    print "</td></table>\n";

    #print "</font></font></b>\n";
    print "</span>";
    print "<br><br><br><br>\n";
    $index--;
    $count--;
  }

  print "<br>\n";

  print "<table width=300 align=center><tr>";
  if ($req_index < $total_entries-1){
    my $x;
    $x=$req_index + $MAX_ENTRY_DISPLAY;
    if($x > $total_entries-1){
       $x = $total_entries-1;
    }
    print "<td align=center>";
    print "<a href=$cgi_script\?entry=$x>";
    print "<img src=/projects/phone/icons/newer.gif border=0 width=102 height=38>";
    print "</a>\n";
    print "</td>";

    #leave some space if older and newer
    if ($req_index-$MAX_ENTRY_DISPLAY >=0){
       print "<td width=50></td>"
    }

  }
 
  if($req_index-$MAX_ENTRY_DISPLAY >=0){
    my $x;
    $x=$req_index - $MAX_ENTRY_DISPLAY;
    print "<td align=center>";
    #print "<a href=$cgi_script\?entry=$x>View Older</a>\n";
    print "<a href=$cgi_script\?entry=$x border=0>";
    print "<img src=/projects/phone/icons/older.gif border=0 width=80 height=38>";
    print "</a>\n";
    print "</td>";
  }
  print "</table>";

}



#==============================================================================
#MAIN

generate_top();

print "<br><br><br><br>\n";


@cgistr = split(/&/, $ENV{QUERY_STRING});

print "<h2>Sorry.</h2>";
print "Dreamhost changed things recently, so this is offline<br>";

#print "Query String is $ENV{QUERY_STRING} <br>\n";
#print "\nThe Entries are:<br>\n";

foreach $i (0 .. $#cgistr)
{
    # convert the "+" to space character
    $cgistr[$i] =~ s/\+/ /g;

    # convert the hex tokens to characters
    $cgistr[$i] =~ s/%(..)/pack("c", hex($1))/ge;

    # split into name and value
    ($name, $value) = split(/=/, $cgistr[$i],2);

    # create the associative element
    $cgistr{$name} = $value;
}

my $entry_id    = $cgistr{entry};
#clean up the numbers and make sure they're integers
if (defined $entry_id){
  #print "ID is valid\n";
  $entry_id = $entry_id + 0; #get rid of leading zeros if any
} else {
  #print "No id value<br>\n";
  $entry_id=-1;
}

dump_starting_at($entry_id);  # $entry_id);


print <<ENDIT;
<br><br><br>

</center>
<font size=-2>
<i>All images copyright AngryNoodle.com. Images may not be rebroadcast
without the written permission Yo Mama.</i>
</BODY>
</HTML>
ENDIT
