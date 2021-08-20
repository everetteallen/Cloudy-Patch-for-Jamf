# Cloudy-Patch-for-Jamf

# Warning: Work in Progress
This project is fluid and evolving as I find out what works so your success with production implementations will depend on your work not mine. 

## Introduction
The Cloudy Patch for Jamf (CPJ) project aims to create a set of Google Cloud Service - Cloud Functions that will use a web hook from Jamf Pro Patch Management to trigger the download of new packages(binary .pkg files) to a GCS bucket, rename with prefix string and suffix with pkg version number, upload to Jamf Pro JCDS for use, and notify via Google Chat api web hooks and Slack api web hooks.  Modularity will be accomplished using a series of cloud functions that respond to pub/sub triggers.  Initially, there are functions working for the web hook listener, the Slack notifier, and the Google Hangouts Chat notifier.  An alpha version of the package downloader that looks up the Patch Title in a Google Sheet returning a download url if available and storing on a Google bucket with rename is also available.  All other functions are concept only.

The idea for this project is born of thinking about the design of other projects like autopkg, jamf api tool, jackalope, Spruce, Prune, etc.  As Apple gets farther and farther away from building true server hardware we are going to need a great deal of this functionality in a serverless, cloud environment like Google Cloud Services.  Be aware that there can be costs running Google cloud functions if the project goes beyond the free tiers or initial credits Google allows.  

> If you were hoping to replace that old MacMini running autopkg - Sorry CPJ won't do that. 

To date I have not seen any code to work with PKG installer files for repackaging, versioning, etc that does not require macOS.  However for sane vendors that produce true, signed, binary packages CPJ could replace some of that work.  This comes with some assumptions: 
1) The Patch Title will not update before the vendor releases an installer package.  Since we can't actually tear apart the package to "version" it the way autopkg processors can, then we have to take this assumption.  Given that Jamf claims a "best effort" turn-a-round on updating patch titles and that vendors usually don't announce new versions until the installers are available, I think this is a good assumption.

2) The installer version available at the time the Patch Title updates is the same as the Patch Title version.  If there are rapid releases one might easily get a newer version of the installer.  I believe this race condition will be rare and worth the risk.

## Overview
Jamf Pro Patch web hook
 A JAMF Web hook will trigger the CPJupdater function when a new software version is added.  Will need to pass the name, latestVersion, and lastUpdate of the software title from the Jamf webhook JSON “event” record to other cloud functions in the chain.  The webhookEvent text from the “webhook” record is also useful for the notification functions to validate the source.
https://www.jamf.com/developers/webhooks/#patchsoftwaretitleupdated
Jamf provides a web hook that contains:


## PatchSoftwareTitleUpdated Web Hook Information

This event is triggered when Jamf Pro receives an update to a patch title it is subscribed to. An example of the data format can be seen below (JSON)
```json
{
    "event": {
        "jssID": 1,
        "lastUpdate": 1506031211000,
        "latestVersion": "61.0.3163.100",
        "name": "Google Chrome",
        "reportUrl": "https://company.jamfcloud.com//view/patch/1/report"
    },
    "webhook": {
        "eventTimestamp": 1553550275590,
        "id": 7,
        "name": "Webhook Documentation",
        "webhookEvent": "PatchSoftwareTitleUpdated"
    }
}
```
This JSON data can be sent manually to trigger the initial cloud function using curl like this example:

```shell
curl -H 'Content-Type: application/json' -X PUT -d '{"event": {"jssID": 1,"lastUpdate": 1506031211000,"latestVersion": "61.0.3163.100","name": "Google Chrome","reportUrl": "https://foo.jamfcloud.com//view/patch/1/report"},"webhook": {"eventTimestamp": 1553550275590,"id": 7,"name": "Webhook Documentation","webhookEvent":"PatchSoftwareTitleUpdated"}}' "https://us-east1-yourcloudfunctionproject.cloudfunctions.net/yourcloudfunctionname"
```
#### Note: this assumes you function is unauthenticated which may not be allowed by some GCS administrators

## Cloud Functions
 It is beyond the scope of this project to explain Google Cloud Functions but Google has great documentation at https://cloud.google.com/functions/docs  I strongly recommend you read at least the Hello World Tutorial before trying to implement CPJ.  I will add a step by step walk-thru for setting up the function runtime environment variables when I have time.
 
### GCF: CPJupdater 
 Receives the web hook from the Jamf Pro Server and parses out the Patch Title name, Patch title version and creates a human-readable date/time string from the lastUpdate value. These are passed as a text message in the PubSub message that are subscribed to by CPJNotifierSlack and CPJNotiferGoogleChat. Finally another PubSub message is sent that contains only the name and version data for use by CPJpkgdownloader

### GCF: CPJpkgdownloader
 Will confirm that a package does not exist in JCDS with the same name (plus prefix) and if not download a package for the software Patch Title determined by looking up the event:name from the web hook JSON in a Google Sheet to return the binary package download url.  The function wil download and store the .pkg file on a GCS bucket.  Then use Pub/Sub message to publish the package name and package version to CPJpkgnamer message.   We will assume that the vendor has proper pkg formatted files and no repackaging will be needed.  Note here that we may need another cloud function to watch for packages to be uploaded to a different GCS bucket and send the same pub/sub to CPJpkgnamer (CPJwatcher) as some packages do not have public download URLs due to being behind a paywall.

### GCF: CPJNotiferGoogleChat
Listens for pub/sub of type CPJNotifier to send message to Google Chat web hook url with the package name, version and date/time.  Use code from HangoutsChatJPUNotifier.

### GCF: CPJNotifierSlack
 Listens for pub/sub of type CPJNotifier to send a message to Slack web hook url with the package name, version and date/time.  

### GCF: CPJpkgCleaner
 Will be triggered by a Google Cron to search the Jamf Pro servers for unused packages using code like BIG-RAT Prune, Spruce , and  JamfAPITool to create a configuration file for Prune or Spruce in a GCS bucket.  This way deletes can be handled as needed with the target being on a monthly basis.  May also want to add the results to BigQuery or Google Sheets for reporting via Google Data Studio.  At present we do not want to automate the deletion of packages.  Should also send pub/sub message of type CPJNotifier with Title “Unused Packages to Check for Delete” and give the Title and version if possible.

