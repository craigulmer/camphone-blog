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

# Account name is the name of the account running the cron job
$ACCOUNT_NAME   = "myuser";
$MAIL_FILE_NAME = "/home/$ACCOUNT_NAME/Maildir/new"; 
$PIC_DIR        = "/home/$ACCOUNT_NAME/pics";
$ARCHIVE_DIR    = "/home/$ACCOUNT_NAME/archives";

$OK_SENDER_EMAIL1 = "14045555555\@tmomail.net";
$OK_SENDER_EMAIL2 = "Craig Ulmer <craig\@craigulmer.com>";

$MAX_MIME_LINES = 10000; #how many lines the mime can be
$DBG_DONT_ERASE = 0;     #set to 1 to avoid clearing mail file

#==[Global Data]==============================================================
$found_something = 0; #Whether we found a picture on this run or not

#=============================================================================
sub my_exit {

  #See if we should archive the mail folder
  if($found_something){

    #Backup this mail with a unique name
    copy($MAIL_FILE_NAME,"$ARCHIVE_DIR/mail-".time);

    #Erase the mail file
    if(!$DBG_DONT_ERASE){
        truncate(IN,0);
    }
  }

  flock(IN,LOCK_UN);
  exit;

}

#=============================================================================
sub chew_to_from {
  
  while ($line = <IN>) {
    chomp $line;
    #print "0: $line\n";
    #last if ($line =~ m/^From /);
    return if ($line =~ m/^From /);
  }

  my_exit();#EOF

}


#=============================================================================
my $data;

sysopen(IN, $MAIL_FILE_NAME, O_RDWR|O_CREAT) or die;
flock(IN, LOCK_EX) or die;


#first time, read to From marker, specifying beginning of message
chew_to_from();

while ($line = <IN>) {

  #Eat until we get the From: field (message header)
  next if ($line !~ m/^From: /);

  #See if sender matches the people we expect
  $line =~ m/^From: (.*)/;
  #print "Answer is $1 vs $OK_SENDER_EMAIL\n";

  if ( ($1 eq $OK_SENDER_EMAIL1) ||
       ($1 eq $OK_SENDER_EMAIL2)   ){
     #print "Hit!: sender is $1\n";
  } else {
     #Not a hit.. discard this message
     #print "Not the right sender.. $1\n";
     chew_to_from();
     next;
  }

  #Hit!: It's from the phone


  #chew until we get file attach, next msg, or eof
  while( $line = <IN> ) {
    chomp $line;
    last if ( $line =~ m/^content-disposition: attachment; filename=.*jpg$/i);
    last if ( $line =~ m/^content-disposition: attachment; filename=\".*.jpg\"$/i); 
    last if ( $line =~ m/^From /); #Next msg
  }

  #Only continue if we hit picture header for mime
  #we would abort only if out of data, or got a new msg header
  next if (!scalar($line));
  next unless (
     ($line =~ m/^content-disposition: attachment; filename=.*jpg$/i) ||
     ($line =~ m/^content-disposition: attachment; filename=\".*.jpg\"$/i) );

  <IN>; #Skip blank line

  undef($buffer);
  undef($data);
  $buffer="";

  my $line_count=0;
  while( $line = <IN> ) {
    chomp $line;
    #print "$line_count: $line\n";
    last if ($line =~ m/^From /);   #end of message
    last if ($line =~ m/^---/);     #end of mime
    last if ($line_count > $MAX_MIME_LINES);
    $buffer = "$buffer$line\n";
    $line_count++;
  }


  #Only continue if really was end of mime
  #next if (!scalar($line)); #EOF
  if ($line !~ m/^---/){
    if($line !~  m/^From /){
      chew_to_from(); #eat until the end of message
    }
    next;
  }

  #Try to decode the picture now
  $data = decode_base64( $buffer );

  if(scalar($data)){

    open(OUT, ">$PIC_DIR/photo-" . time . ".jpg");
    syswrite(OUT, $data);
    close(OUT);
    sleep(2); #Make sure we don't kill previous file
    $found_something=1;

  } else {
    #print "No data?\n";
  }

  chew_to_from();
  
}

my_exit(); #Safely leave
