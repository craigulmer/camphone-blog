#!/usr/bin/perl -w

use Fcntl ":flock";


my $AT_HOME = 0;
my $ALLOW_POSTING = 1;

if($AT_HOME){
  $html_dir    = "/var/www/html"; #Home use
} else {
  $html_dir = "/path/to/html";
}



my $phone_dir = "$html_dir/projects/phone";
my $pics_dir    = "$phone_dir/pics";
my $com_dir     = "$phone_dir/comments";

my $img_link    = "/projects/phone/pics";

my $cgi_script  = "/cgi-bin/phone.cgi";

my $ns_vdir     = "/noodlespeak";

my $MAX_ENTRY_DISPLAY = 5;

my $MAX_CONTENT_LENGTH = 4096; #how much data one can post to us legally

# Posting password is md5 digest encoded here. You need to stick the
# hex values in PPWD_THING. No this is not meant to be secure. It's just
# a way to not be low hanging fruit for SEO jerks.
my $PPWD_FRONT = "People who make ";
my $PPWD_BACK  = " are wrong.";
my $PPWD_THING = "INSERT_MD5_HEX_DIGEST_HERE";

#-- Globals -------------------------------------------------------------------
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
sub dump_error {
  my $etext = shift(@_);
  print "<h1>Whatcha talking about..?</h1>";
  print "$etext\n";
  print "</body></html>";
  exit;

}
#==============================================================================
sub dump_back  {
  my $index = shift(@_);

  print "<br><br><center><a href=/cgi-bin/phone.cgi?entry=$index>";
  print "<img src=/projects/phone/icons/back.gif border=0 width=74 height=38>";  
  print "</center><br><br>\n";
}
#==============================================================================
sub fixup_id{
   my $id = shift(@_);


   #clean up the numbers and make sure they're integers
   if (defined $id){

     if($id =~ /\D/){
       dump_error("You gave me a non-integer entry id? $id"); 
     }

     $id = $id + 0; #get rid of leading zeros if any
   } else {
     dump_error("You gotta give me an ID for the picture<br>(Hint:  ?entry=1)<br>");
   }

   return $id;
}
#==============================================================================
sub get_picname_from_id {
   my $id = shift(@_);

   #See how many files there are
   opendir(PDIR, "$pics_dir") or die "Couldn't get Directory\n";
   my @allfiles = grep  { /.jpg/ && !/~/ } readdir PDIR;
   closedir PDIR;
   @allfiles = sort(@allfiles);

   #See if we're in range
   my $total_entries = scalar(@allfiles);
   if(($id<0) || ($id>=$total_entries)){
       dump_error("You gave me an entry id I don't know about: $id\n");
   }

   return @allfiles[$id];

}
#==============================================================================
sub generate_pic {

    my $pic_name = shift(@_);
    my $mtime = (stat("$pics_dir/$pic_name"))[9];

    print "<br><br><center>";
    print "<img src=$img_link/$pic_name border=2><br>\n";
    print "<span class=\"pdate\">";
    #print "<b><font face=Verdana><font color=#000055><font size=-2>";
    printf "Posted: %s \n", scalar localtime $mtime;
    print "</center>\n";
    print "<br><br><br>\n";

}


#==============================================================================
sub dump_comments {

 my $entry  = shift(@_);
 $entry =~ s/\.jpg//;

 print "<h1>Comments:</h1>\n";

 if ( ! (-e "$com_dir/$entry.txt") ){
   print "<br><center><font size=+1>No comments so far!</font></center><br>";
 } else {

   my $even=0;
   open(COMMENTS, "$com_dir/$entry.txt") or die "Couldn't get entry\n";

   print "<center>\n";
   print "<table class=\"commentBox\" cols=1>\n";

   while (<COMMENTS>){
     chomp;
     my $pname = $_;

     $_ = <COMMENTS>;
     chomp;
     my $paddress = $_;

     $_ = <COMMENTS>;
     chomp;
     my $pdate = scalar localtime $_;

     $_ = <COMMENTS>;
     #extra field for IP

     if ($even){
          print "<tr><td class=\"commentEven\">\n";
     } else {
          print "<tr><td class=\"commentOdd\">\n";
     }
     $even=!$even;

     $in_line=<COMMENTS>;
     while( $in_line !~ /AN_COMMENT_TAG_BOYEE/ ){
	print "$in_line";
	$in_line=<COMMENTS>;
     }

     if ($paddress){
       print "<br><br><i>Posted By: </i>";
	 if ($even){
              print "<a href=$paddress rel=\"nofollow\" class=\"aodd\" target=\"_top\">$pname</a>"; 
         } else {
              print "<a href=$paddress rel=\"nofollow\" target=\"_top\">$pname</a>";
         }   
     } else {
       print "<br><br><i>Posted By: </i><b>$pname</b>";
     }
     print "<br><font size=-1>$pdate Pacific</font>";
     print "</td></tr>\n";
   }

   print "<center>\n";
   print "<table class=\"commentBox\" cols=1>\n";
 
   print "</table>\n";
   print "</center>\n";
 }

}
#===============================================================================
sub dump_add_comment_box {

  my $entry_id = shift(@_);

  if(!$ALLOW_POSTING){
    dump_no_posting_error();
    return;
  }


print <<END_ADD_COMMENT;

<br><h1>Add Your Comments:</h1>

<center>

<form name=\"commentForm\" method=\"post\" action=\"/cgi-bin/phone-comment.cgi?entry=$entry_id\">
<input type=\"hidden\" name=\"comment_entry_id\" value=\"$entry_id\">

<table class="commentOutline"><td>
<table class="commentTable">
<tr>
  <td class="commentLabel" >Name :</td>
  <td><input type="text" name="name" size=10 class="commentBox"></td>
</tr>

<tr>
  <td class="commentLabel">Link (optional) :</td>
  <td><input type="text" name="link" size=10 class="commentBox" value="http://"></td>
</tr>


<tr>
  <td class="commentLabel">Comments :</td>
  <td><textarea name="comment_text" cols=60 rows=10 wrap=soft class="commentEntry"></textarea></td>
</tr>

<tr>
  <td class="commentLabel" vertical-align="middle">Posting Password* :</td>
  <td>
   <table width=100%>
     <tr>
       <td class=dol>"$PPWD_FRONT <input type="text" name="postpwd" size=10 class="commentPostPwd" value="">$PPWD_BACK"</td>
       <td><input type="submit" name="go" value="Post it!"></td>
     </tr>
   </table>
  </td>
</tr>

</table>

</td>
</table>


<center><br>
<i>Note: <b>Plain-text</b> only (no HTML codes)</i><br><br>
</center>
<br><br>

<table class="commentOutline"><td>
<table class="commentTable" cellspacing=0 cellpadding=20>
<td><b>* Posting Password</b>
<p class=dol>It's sad that I have to put some form of access control on AngryNoodle, but I've had problems
with spammers filling up my comment system with ads (500 comments with the same link on one
blog post? Just how dumb do you think Google is?). I've looked at a few ways of dealing with
comment-spam, but there doesn't seem to be a good solution. Therefore, I've put a simple password
access control on the posts to prevent blind scripts from disrupting things. If you know me,
you've probably seen me use the above quote in various places. The missing word is the posting
password. No, it's not the easiest word to spell, but it's also not something that's easy to
figure out with google. Don't write about the word in your comment. If you're stumped,
write Amy or myself and we'll tell you what it is.</div>
</td>
</table>
</td></table>




</form>
</center>
END_ADD_COMMENT

}

#==============================================================================
sub strip_html_codes {
   $_ = shift(@_);
   s/</&lt;/g;
   s/>/&gt;/g;

   s/AN_COMMENT_TAG_BOYEE//g;

   return $_;
}
#==============================================================================
sub fixup_link {
   $_ = shift(@_);
   chomp;
   $_ = strip_html_codes($_);

   if($_ eq "http://"){
     $_="";
   }

   return $_;
}
#==============================================================================
sub fixup_text {
   $_ = shift(@_);
   $_ = strip_html_codes($_);
   s/\n/<br>/g;
   s/\r/\n/g;   #chop up lines for easier reading on back end

  return $_;
}
#==============================================================================
sub dump_overpost_error {

print <<END_OVERFLOW_TEXT;

<h1>Overpost detected</h1>
<font size=+1>Sorry dude, that's way too long. I have to reject posts that
are longer than a certain size, or else 
<a href=http://www.kellegous.com>The Kellegous</a> will just
fill us up with Irish poetry. Hit the back button on your
browser and try to be a bit more concise. I'll wait for you.</font>
<br><br><br><br><br><br>

END_OVERFLOW_TEXT

}
#==============================================================================
sub dump_no_posting_error {

print <<END_NOPOST_TEXT;

<h1>Posting Disabled</h1>
<font size=+1>Sorry. Someone has been posting spam to the comments, so I've
had to disable it for now.</font>
<br><br><br>
END_NOPOST_TEXT

}
#==============================================================================
sub dump_bad_passwd {

print <<END_BAD_PASSWD;
<h1>Posting Password Error</h1>
<font size=+1>Sorry, that isn't the right posting password. Use the back
button in your browser to try again.<br>
If you cannot remember the password, ask Craig or Amy.</font>
<br><br><br>
END_BAD_PASSWD
}
#==============================================================================
sub parse_form_data {
  my %form_data;
  my $name_value;
  my $in_length;

  my @name_value_pairs = split /&/, $ENV{QUERY_STRING};

  #print "<h2>Parsing form data</h2>\n";

  #Check to make sure Kelly isn't sending us a core file
  $in_length=$ENV{CONTENT_LENGTH};
  if ($in_length > $MAX_CONTENT_LENGTH){
       dump_overpost_error();
       read(STDIN, $query, $in_length ) == $in_length or return undef;
       return undef;
  }

  if ($ENV{REQUEST_METHOD} eq 'POST'){
    my $query = "";
    read(STDIN, $query, $in_length ) == $in_length or return undef;
    push @name_value_pairs, split /&/, $query;
  } else {
    return undef;
  }

  foreach $name_value ( @name_value_pairs ) {
    my ($name, $value) = split /=/, $name_value;

    $name =~ tr/+/ /;
    $name =~ s/%([a-f0-9][a-f0-9])/chr( hex($1) )/egi;

    $value = "" unless defined $value;
    $value =~ tr/+/ /;
    $value =~ s/%([a-f0-9][a-f0-9])/chr( hex($1) )/egi;

    $form_data{$name} = $value;

    #print "$name = $value<br>\n";
  }

  #print "$ENV{REMOTE_ADDR}<br>\n";

  #fixup entry name and translate to a file
  my $entry_id = fixup_id( $form_data{entry}  );
  my $pic_name = get_picname_from_id($entry_id);
  my $entry = $pic_name;
  $entry =~ s/\.jpg//;

  #print "Entry is $entry";

  if (! (-e "$pics_dir/$pic_name") ) {
     dump_error("No target..? $pics_dir/$pic_name");
     return undef;
  }

  #extract the post params
  $form_data{postpwd}      = fixup_text($form_data{postpwd});
  $form_data{name}         = strip_html_codes($form_data{name});
  $form_data{link}         = fixup_link($form_data{link});
  $form_data{comment_text} = fixup_text($form_data{comment_text});


  #Instead of storing clear password in this script, we md5 encode
  # the password. Thus we must encode user's password as well
  use Digest::MD5 qw( md5_hex );
  my $hex_digest = md5_hex( $form_data{postpwd});

  #print "<h2>Hex dig is $hex_digest<h2>";



  #if($form_data{postpwd} ne $PPWD_THING){
  if($hex_digest ne $PPWD_THING){
    dump_bad_passwd();
    return;
  }

  if ("$form_data{name}" eq "") {
     $form_data{name} = "A nameless dork";
  }

  if ($form_data{comment_text} eq ""){
    print "<h2>No comment detected</h2>";
    return;
  }

  if(!$ALLOW_POSTING) {
    dump_no_posting_error();
    return;
  }

  my $mtime = time;

  #print "<h2>About to do $com_dir/$entry.txt</h2>";

  open  COMMENTS, ">>$com_dir/$entry.txt" or die "Can't write?";

  flock COMMENTS, LOCK_EX; #--------------------

  print COMMENTS "$form_data{name}\n";
  print COMMENTS "$form_data{link}\n";
  print COMMENTS "$mtime\n";
  #printf COMMENTS "%s Pacific\n", scalar localtime $mtime;

  print COMMENTS "$ENV{REMOTE_ADDR}\n";
  print COMMENTS "$form_data{comment_text}\n";
  print COMMENTS "AN_COMMENT_TAG_BOYEE\n";

  flock COMMENTS, LOCK_UN; #--------------------

  close COMMENTS;

  return %form_data;
}

#==============================================================================
#MAIN

generate_top();
print "<br><br>\n";

#--first take care of any incoming form data----------
parse_form_data();


#--Normal stuff for extracting args-------------------
@cgistr = split(/&/, $ENV{QUERY_STRING});

#print "Query String is $ENV{QUERY_STRING} <br>\n";

foreach $i (0 .. $#cgistr) {
    # convert the "+" to space character
    $cgistr[$i] =~ s/\+/ /g;

    # convert the hex tokens to characters
    $cgistr[$i] =~ s/%(..)/pack("c", hex($1))/ge;

    # split into name and value
    ($name, $value) = split(/=/, $cgistr[$i],2);

    # create the associative element
    $cgistr{$name} = $value;
}
#-----------------------------------------------------

my $entry_id = fixup_id( $cgistr{entry} );
my $pic_name = get_picname_from_id($entry_id);

#print "<h2>Entry is $entry_id: $pic_name</h2>";

generate_pic($pic_name, $entry_id);

dump_comments($pic_name);
dump_add_comment_box($entry_id);
dump_back($entry_id);
