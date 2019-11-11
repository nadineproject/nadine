Nadine Structure
================

Overview
--------

Nadine is comprised of four applications: Members, Staff, Admin, and Tablet.

**Members** is the member facing application. We consider members to be users with active resource allocations. **Staff** is the application used by staff members to help with the overall management of the community. **Admin** is the application in which only application administrators can access as it has absolute access to data. **Tablet** is the application used for user sign-ins and for the interaction expected at the entrance of a space and greeting a new or returning user of the space.

Members Application
-------------------

This application is what members will use to connect with each other, the coworking space staff, and greater community.

.. note::

  Much of the information given by members and organizations is designated as either public (viewable by current members) or private (only viewable by staff and that specific member). This is clearly indicated to members and they opt in to sharing whatever of that information with which they are comfortable.

In the Members Application there are profiles for both members and organizations/companies. Each have a photo or logo, URLS they would like others to see, a short bio, and tags. While the listed items are public, privately the members and organizations can see emergency contacts, billing history, signed documents (such as a membership agreement), and their user activity.

A member and an organization can edit their profiles as often as they would like. One setting, though, that is set by application administrator is whether or not members are allowed to upload their own user photos. That setting is entitled ALLOW_PHOTO_UPLOAD. More information in :doc:`Changing Application Settings <settings>`.

Other features of the Members Application are the calendar of events, ability to subscribe and unsubscribe from mailing lists, Slack invitation (if allowed in Settings), and the general ability to see who the other members and organizations are and to make a request to connect.

One feature, tags, are interests they can share which are then sortable and searchable by other members and organizations. This allows a space to see how organizations self identify their industries and also what their members are doing.

The Members Application is laid similarly in the views and the templates.

* connect
* core
* events
* organization
* profile
* tags



Staff Application
-----------------

The Staff Application allows the staff of a space to best manage memberships and the tasks required to run the space. It is the application designed for staff to easily track space usage, review billing and deposits, and edit member information if/when needed.

The navigation of the Staff Application includes:

* Tasks/ToDo
* Member List
* Activity
* Billing
* Stats
* Logs
* Lists
* Settings

Tasks/Todo
//////////

This section of the Staff Application deals with tasks that staff must complete. Tasks can be assigned to specific staff members or left available for anyone to complete and mark as such. This is the default home page for a staff member.

Member List
///////////

Member List shows all members in a sortable manner and then allows a staff member to edit any person's information as needs.

Activity
////////

Activity is for recording any members particular use of the space and to generate reports on past usage and membership levels.

Billing
///////
It is important to know that Nadine does not store any person's credit card information. Nadine in its current iteration uses a USAEpay integration for billing. In this section of the application, staff can track payments, generate reports, and run the daily billing.

Logs
////

Logs show device and user logins to the local internet. To know the user, the system remembers devices after a member has logged into Nadine from that computer. This allows us to better track use of space and to make sure that a member is using the space per their membership.

Lists
/////

These pages are for the management of whatever mailing lists a space might have and the Slack channel, if a space has it.

Settings
////////

Under Settings, staff has the ability to edit different elements of the application as well as see the settings as set by the Nadine Admin. Options from the Settings dropdown include:

- **Help Texts** - These are the documents for frequently asked questions. Each will have it's own page which members will be able to review.
- **MOTD** - MOTD stands for Message of the Day. This is the greeting which is presented on the home screen of the Tablet Application.
- **Membership Packages** - Allows staff to create and edit the default subscriptions and pricing for membership packages
- **Edit Rooms** - Staff can add and edit the details of rooms which are available for users to reserved


Admin
-----

Like most admin applications, this has absolute access to user and space data. As stated before, though, this does not include any credit card information. Only application administrators have access to this part of Nadine.

Tablet Application
------------------

The Tablet is designed for use on an iPad at the entry of a space as a sort of portal. The user has access to sign in and see who else is in the space from this. Additionally, a user can sign documents such as a membership agreement.
