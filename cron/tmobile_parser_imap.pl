#!/usr/bin/perl -w
#
# File:    tmobile_parser.pl
# Author:  Craig Ulmer (w/ help from Kelly Norton & John Lockhart)
# Purpose: This script is to be used as a cron job. It examines an email
#          inbox to see if there are any new mail messages from a few
#          specified addresses. For these specified senders, it will examine
#          the messages to see if there are mime picture attachments. If
#          there are, the pictures will be extracted and stored with unique
#          file names in a designated directory. The script will then
#          backup the mail to an archive directory, and then zero out the
#          mail file (to prevent dupes). 
#
#         Update: increased mime lines max. 10000 cut off at 500KB
#         Update: added support for google mail's version so Boost
#                 mobile will work. Had to change some parsing. Still
#                 messy
# 
#         Update: dreamhost stopped supporting shell email. Had to 
#                 add a filter option in Mail->MessageFilters that
#                 forwards data to shell account.
#
#         Update: Changed from email for cingular->att.net June 4, 2007
#              
#         Update: Added <> to ok email address list - December 17, 2006
#
#         UPDATE: Added support for Cingular. Also, use ImageMagik to
#                 downsample images to a width of 640 pixels.
#                      -December 11, 2005
#                      
#
#         UPDATE: this is a quick mod to try and get imap working right.
#                 the script now reads through all files in the maildir/new
#                 directory, and parses them. Have not tested on multi-mail
#                 file.
#                       -August 29, 2004
#
#
#          currently:
#           -Verifies sender address
#           -Discards simple bad data (empty/too much mime, bad format)
#
#          Future:
#           -Is flocking set right? What if data arrives when processing?
#           -Could split data to different dirs, based on sender's id
#

use Fcntl qw(:DEFAULT :flock);
use File::Copy;
use MIME::Base64;

use Image::Magick;

# Account name is the name of the account running the cron job
$ACCOUNT_NAME   = "myuser";
$MAIL_DIR       = "/home/$ACCOUNT_NAME/Maildir/new";
$PIC_DIR        = "/home/$ACCOUNT_NAME/tmobile/pics";
$PIC_BIG_DIR    = "/home/$ACCOUNT_NAME/tmobile/pics_big";
$ARCHIVE_DIR    = "/home/$ACCOUNT_NAME/tmobile/message_archive";

$TARGET_WIDTH   = 640;
$PIC_COMMENT    = "Copyright AngryNoodle.com";

# Accept emails from different places. Sometimes phones change these 
@OK_SENDER_EMAILS = ( 
            "9255555555\@mms.mycingular.com",
            "19255555555\@mms.mycingular.com",
		      "<9255555555\@mms.mycingular.com>",
		      "9255555555\@mms.att.net",
		      "<9255555555\@mms.att.net>",

		      "9256666666\@mms.mycingular.com",
		      "19256666666\@mms.mycingular.com",
		      "<9256666666\@mms.mycingular.com>",
		      "9256666666\@mms.att.net",
		      "<9256666666\@mms.att.net>",

            "George Burdell <george.burdell\@gmail.com>",
            "Bob Bozzo <bob.bozzo\@gmail.com>",		      
		      "Craig Ulmer <craig\@craigulmer.com>" );





$MAX_MIME_LINES = 30000; #how many lines the mime can be
#$DBG_DONT_ERASE = 0;     #set to 1 to avoid clearing mail file


#==[Global Data]==============================================================
$found_something = 0; #Whether we found a picture on this run or not

#=============================================================================
sub downsample_file {

  my ($file_name) = @_;

  my $image;
  my $x;
  my $width;
  my $height;
  my $scale;

  $image = Image::Magick->new;
  $x = $image->Read("$PIC_BIG_DIR/$file_name");
  warn "$x" if "$x";

  $width  = $image->Get('width');
  $height = $image->Get('height'); 

  #-- Just move smaller pics to the main dir ---
  if($width <= 640) {
    move("$PIC_BIG_DIR/$file_name","$PIC_DIR/$file_name") or die "no move on $file_name?";
    return;
  }

  #--Scale it to the right size----------------
  $scale = $TARGET_WIDTH / $width;
  $height = $height * $scale;
  $x = $image->Resize(width=>$TARGET_WIDTH, HEIGHT=>$height);

  #--Reset the comment-------------------------
  $x = $image->Comment($PIC_COMMENT);
  warn "$x" if "$x";

  $x = $image->Write("$PIC_DIR/$file_name");
  warn "$x" if "$x";
}


#=============================================================================
sub close_file {

  my $mail_file_name = shift @_;

  #print "Close $mail_file_name\n";

  #flock(IN,LOCK_UN);
  close(IN);

  if ($found_something) {
    #Backup this mail with a unique name
    #copy($mail_file_name,"$ARCHIVE_DIR/mail-".time);

    move($mail_file_name,"$ARCHIVE_DIR/mail-".time) or die "no move? of $mail_file_name to $ARCHIVE_DIR/mail-xx";

    #Erase the mail file
    #tuncate(IN,0) if(!$DBG_DONT_ERASE);

  }



  close IN;
}


#=============================================================================
sub chew_to_from {
  
  while ($line = <IN>) {
    chomp $line;
    #print "0: $line\n";
    #last if ($line =~ m/^From /);
    return 1 if ($line =~ m/^From /);
  }

  return 0;

}
#=============================================================================
sub validate_sender {

  my $from_line = shift @_;

  $from_line =~ m/^From: (.*)/;

  foreach (@OK_SENDER_EMAILS) {
    #print "Checking $_ to compare to $1\n";
    return 1 if ($1 eq $_);
  }

  return 0;

}
#=============================================================================
sub isMimePicStart {
  my $line = shift @_;

  if ( ( $line =~ m/^content-disposition: attachment; filename=.*jpg$/i)      ||
       ( $line =~ m/^content-disposition: attachment; filename=\".*.jpg\"$/i) || 
       ( $line =~ m/^content-disposition: inline;filename=(.*)jpg$/i)         ||    #att march2010
       ( $line =~ m/^content-disposition: attachment; filename=\"(.*).jpg\"$/i) || #boost gmail
       ( $line =~ m/^content-type: image\/jpeg/i ) ){ #Boost phone

      return 1;
      #last if ( $line =~ m/^content-disposition:/i); #for cingular
  }
  return 0;
}
#=============================================================================
sub parse_file {
  
  my $mail_file_name = shift @_;
  my $line;
  my $data;
  my $fname;

  #print "Parsing $mail_file_name\n";

  sysopen(IN, $mail_file_name, O_RDWR|O_CREAT) or die;
  flock(IN, LOCK_EX) or die;



  while ($line = <IN>) {

    #Eat until we get the From: field (message header)
    next if ($line !~ m/^From: /);

    #Make sure it came from right person
    if ( !(validate_sender( $line )) ) {
      #Not a hit.. discard this message
      print "Not the right sender..\n";
      #return if !(chew_to_from());
      next;
    }

    #Hit!: It's from the phone
    $found_something=1;

    #chew until we get file attach, next msg, or eof
    while( $line = <IN> ) {
      chomp $line;
      ##print "--$line\n";
      last if (isMimePicStart($line));
      last if ( $line =~ m/^From /); #Next msg
    }

    #Only continue if we hit picture header for mime
    #we would abort only if out of data, or got a new msg header
    #the disposition should be last line before plain mime text. we only pass on the binary
    #data, not the header info
    next if (!scalar($line));
    next unless (isMimePicStart($line));

    #Need to skip rest of header - note: no chomp. May need to rollback
    while( $line = <IN> ){
      #print "xx>'$line'\n";
      last if ($line =~ m/^From /);
      last if ($line eq "\n");
    }
    if($line =~ m/^From /){
      seek(IN, -length($line), 1); # place the same line back onto the filehandle
      last;
    }


    undef($buffer);
    undef($data);
    $buffer="";

    my $line_count=0;
    while( $line = <IN> ) {
       chomp $line;
       #print "$line_count: $line\n";
       last if ($line =~ m/^From /);   #end of message
       #last if ($line =~ m/^---/);     #end of mime
       last if ($line =~ m/^--/);     #end of mime
       last if ($line_count > $MAX_MIME_LINES);
       $buffer = "$buffer$line\n";
       $line_count++;
    }


    #Only continue if really was end of mime
    #next if (!scalar($line)); #EOF
    if ($line !~ m/^--/){
      if($line !~  m/^From /){
        chew_to_from(); #eat until the end of message
      }
      next;
    }

    #print "Buffer==\n$buffer\n===";
    #Try to decode the picture now
    $data = decode_base64( $buffer );

    if(scalar($data)){

      #open(OUT, ">$PIC_DIR/photo-" . time . ".jpg");
      $fname = "photo-" . time . ".jpg";
      #print "Source is $fname\n";
      open(OUT, ">$PIC_BIG_DIR/$fname");
      syswrite(OUT, $data);
      close(OUT);
      downsample_file($fname);

      sleep(2); #Make sure we don't kill previous file
      $found_something=1;

    } else {
      #print "No data?\n";
    }
  
  }


}


#=============================================================================


opendir(MDIR, $MAIL_DIR);
@all_files = grep { $_ ne '.' and $_ ne '..'} readdir MDIR;
@all_files = sort(@all_files);

#print "Starting\n";

for $mail_file (@all_files) {

  $found_something = 0;
  #print "$mail_file\n";
  parse_file("$MAIL_DIR/$mail_file");
  close_file("$MAIL_DIR/$mail_file");
}






