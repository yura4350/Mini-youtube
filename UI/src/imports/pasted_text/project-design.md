High-level project design:
Use Cases
User Accounts and Preferences (USER_ACCOUNTS_PREFERENCES-NN):
Registration (Create account)
User signs up with email, username, password (and any additional data we need)
System validates user input (email format, password length, etc.)
System check for duplicate emails/usernames
System hashes and stores password
Login
User logs in with their credentials
System verifies password, return session token(?)
Handle invalid login
System return error for incorrect credentials
System does rate limiting after certain number of failed attempts
Reset password
User requests reset
System generates temporary password (or some kind of token)
User submits new password and temporary password (or token)
Temporary password gets expired
Logout
User clicks logout button
System redirects to main page (non-logged in version)
View user profile
User clicks on profile button and views their profile
Edit user profile
User updates profile (e.g. new username) via edit/save button
System validates user input
Privacy settings
User toggles privacy-related settings (e.g. public/private profiles, etc.)
Notification settings
User configures push notification, chat notification (from real-time chat/messaging)
UI settings
User decides the layout/order of videos being displayed, size of the video screen, etc.

Admin Dashboard (ADMIN_DASHBOARD-NN):
View system health
Admin clicks on the button to check health
Systems sends a request to /health endpoint
Admin sees the result of the reply
View User counts
Admin sees the current real-time user counts
Real-time user counts are consistently updated with the calls to some endpoints of REST API
Admin sees the updated user counts real-time
View logs
Admin sees the current logs
Real-time logs are consistently updated with the calls to some endpoints of REST API
Admin sees the updated user logs real-time
Ban user
Admin selects the user to ban them in the UI
The patch request is sent to the backend 
Frontend makes another request to the backend and gets updated
Reset password
Admin can reset their own password
The request is sent to the backend
Backend sends the email through email service
Admin restores the password
Password changes in the database
Admin can log in now
Delete content
Admin deletes certain video
Patch request sent to the database (or wherever we store videos)
View metrics
Admin can go to the metrics window
Metrics are updated in real time through sending the get requests to the backend

Dashboard and Search (USER_DASHBOARD_SEARCH-NN):
Looking for Videos
User login.
The system detects whether the user has any history:
If there is, the system generates video recommendations based on trending algorithms and the user’s watching history.
If there is not, the system generates recommendations based solely on trending topics and location-based hotspots.
User selects a video from the recommendation feed.
The system retrieves the video metadata and stream URL, adding the new video history to this user’s information.
The system initiates the video player and begins streaming.
Search Input
User enters keywords into the search bar on the homepage.
The system provides real-time search suggestions based on the input.
The system filters and ranks videos based on relevance, keywords, and user preferences.
Subscription list
User views subscription tab, which shows the latest videos from subscribed creators (in chronological order)
Recently watched
User views recently watched videos
Notification tab
 User sees notification inbox that contains recent notifications, marked read or unread
Search history
When clicks on the search bar, the system displays a short list of recent search history
Subscribed channel tab
User views a list of channels currently subscribed to
User can edit channel-specific settings (unsubscribe, enable/disable notification from the channel, etc.)
Uploaded videos tab
User views a list of uploaded videos by that user
User Profile
When clicks on the Profile section of the Dashboard, the user will be navigated to the Profile page.
The system retrieves and displays the current profile data (Name, Bio, Avatar…)


Concurrent CRUD Access (CRUD-NN):
Atomic View Count Update
Multiple users are watching the same viral video simultaneously, which will cause race conditions.
The system uses an atomic increment (maybe in the redis) and sync the batch totals asynchronously to the database.
Video Metadata Edit
User A changes the Title of the video.
User B changes the Description of the video seconds later.
The system uses a version column to update the information of the video.
Invalid video metadata during upload
User submits empty title, overly long description, etc. 
Reject request to upload
Unique email and username 
Two users try to use the same email or username
System only allows one of the two requests

Intelligence (INTELLIGENCE-NN::
AI-summarize
The button to AI-summarize is clicked by user
The request is sent to the backend
Based on the subtitles the LLM agent is called to summarize the video
The summary is returned to the frontend
User can tag their content
The user adds a tag to the content on the frontend
The patch request is sent to the backend
The database is updated to reflect the tag
User can see the tags
When the user looks at the video
The request to backend is sent
Backend fetches database and returns tags
Tags are displayed with a video
User gets recommended the videos based on the title and author history
When the dashboard is uploaded, Intelligence microservice is called to calculate recommendations
Backend determines recommended videos
Recommended videos are shown in the user feed

Communication:
New video notification
If there is a new video uploaded to a channel which the user is already subscribed to, system pushes notification
System stores notification in an inbox
Notification Inbox
User opens notification tab (or possibly a dashboard) and sees a list of unread notifications
System marks as read if user clicks to check the notification
Real-time chat
If multiple users are online, the message is delivered instantly
(One real-time chat for each video/trending video/live stream, etc.)
Subscription notification
User subscribes to a new channel
System sends a notification to confirm subscription
Chat notification
If there is an active conversation in a previously participated chat, system sends a notification to the user
Test Scenarios
User Accounts and Preferences:
Check Registration Functionality
Check Login Functionality
Valid login
Invalid Login
Check reset password functionality
Check logout functionality
Check user profile view functionality
Check edit user profile functionality
Check privacy settings functionality
Check edit
Check if privacy settings configure privacy properly
Check notification settings functionality
Check editing
Check if notification settings configure notifications properly
Check UI settings
Check editing
Check if UI settings configure UI properly

Admin Dashboard:
Check if admin can view system health
Check if admin can view user counts
Check if admin can view logs
Check if admin can bas users
Check if admin can reset their password
Check if admin can delete content
Check if admin can view metrics

Dashboard and Search:
Check if the user dashboard displays the appropriate videos
Check if you can search the videos
Check if after search the appropriate videos pop
Check if you can search through the tags
Check if user has a subscription list
Check if a user has recently watched tab with recently watched videos
Check if user has a notification tab with recent notifications
Check if user has a search history displayed when he searches

Concurrent CRUD access:
Check that videos work properly if several people are watching it simultaneously
Check that the video metadata is updated in real time (author changes the title, user sees it if they refresh the page)

Intelligence:
Check if AI-summarization works properly
Check if users can tag their content
Check if users can see the tags
Check if user gets recommended proper videos

Communication:
Check that users get new video notifications
Check that notification inbox is working
Check that real-time chat is working
Check that there is a subscription notification
Check if chat notifications are handled properly

APIs
In general, we will strive to have an API for every microservice we have.
User Accounts and Preferences API
Purpose: Handles the full lifecycle of a user, from registration and secure login to personalized UI and privacy settings.
Method    Endpoint    Description
POST    /auth/register    Create account with email, username, and hashed password.
POST    /auth/login    Validate credentials and return a session token/JWT.
POST    /auth/logout    Invalidate the session and redirect to the landing page.
POST    /auth/reset-password    Request a reset token or submit a new password.
GET    /user/profile/{id}    Retrieve public profile data (Bio, Avatar, etc.).
PATCH    /user/profile/edit    Update username or profile details.
PATCH    /user/settings/privacy    Toggle public/private profile visibility.
PATCH    /user/settings/notifications    Configure push and chat notification preferences.
PATCH    /user/settings/ui    Save custom layout, video size, and display order.
2. Admin Dashboard API
Purpose: Provides elevated access for administrators to monitor system health, moderate content, and manage users.
Method    Endpoint    Description
GET    /admin/health    Check the status/health of all running microservices.
GET    /admin/users/count    Retrieve real-time count of active and total users.
GET    /admin/logs    Fetch real-time system and error logs.
PATCH    /admin/users/{id}/ban    Restrict a specific user's access to the platform.
POST    /admin/auth/reset    Allow admin to reset their own password via email service.
DELETE    /admin/content/{v_id}    Remove a video from storage and the database.
GET    /admin/metrics    Retrieve real-time performance and usage metrics.
3. Dashboard and Search API
Purpose: Powers the primary user interface, discovery algorithms, and keyword queries.
Method    Endpoint    Description
GET    /dashboard/recommend    Get videos based on history or trending/location hotspots.
GET    /search    Filter and rank videos based on keywords and relevance.
GET    /search/suggestions    Provide real-time keyword suggestions as the user types.
GET    /search/history    Display a list of the user's recent search queries.
GET    /subscriptions/feed    List latest videos from subscribed channels (chronological).
GET    /user/history/watched    List recently viewed videos for the user.
GET    /user/notifications    Fetch recent alerts (read/unread) from the notification inbox.
4. Concurrent CRUD Access API
Purpose: Ensures data integrity during high-traffic events, such as viral video view spikes or simultaneous metadata edits.
Method    Endpoint    Description
POST    /crud/check    Validate input constraints (email uniqueness, title length).
POST    /crud/add    Handle new video uploads and initial metadata entry.
POST    /crud/watch    Atomic view count increment (buffered via Redis).
PATCH    /crud/update    Edit video metadata using version-locking to prevent race conditions.
5. Intelligence API
Purpose: Leverages LLM agents and recommendation engines to enhance content value and discoverability.
Method    Endpoint    Description
GET    /ai/health    Check the availability of the LLM/Intelligence service.
POST    /ai/summarize    Call the LLM agent to summarize a video via its subtitles.
POST    /ai/tagging    Add or automatically generate tags for specific content.
GET    /ai/tags/{v_id}    Retrieve and display all tags associated with a video.
GET    /ai/recommend/logic    Calculate and return recommended videos for the user feed.
6. Communication API
Purpose: Manages the real-time social layer, including chat rooms and the notification delivery pipeline.
Method    Endpoint    Description
POST    /comm/notifications    Create and route new video or subscription alerts.
PATCH    /comm/notifications/read    Mark a notification as read when clicked by the user.
WS    /comm/real-time-chat    Establish a WebSocket connection for instant messaging on videos.
POST    /comm/chat/notify    Send a push notification for active chat conversations.
User Data Requirements
User account data: required for authentication
Email: 
used for login, password recovery, and possibly communication
Retained until account deletion
Username:
Unique identifier shown to other users on the platform
Retained until account deletion
Password:
Used for authentication (login)
Never stored in plain text (will be hashed)
Retained until account deletion
Profile & user preferences data: enables personalization; stored until user update or deletion
Profile data
Privacy settings
Notification settings
UI settings
User activity data: 
Watch history
Tracks videos the user viewed
Tracked to generate recommendations
Retained until user clear history, or automatically deleted after a certain period of time (e.g. 30 days). Users will have control over this
Search history
Stores recent search queries, improves search suggestions
Retained until user clears history, or automatically deleted after a certain period of time (e.g. 7 days). Users will have control over this
Subscription data
To enable core features (subscription), we need to keep a list of which channels the user is subscribed to.
Retained until account deletion
Communication data
Notifications
Stores user notifications to keep users informed about their account activity
Retained for a short period of time (or until user clears notifications)
Chat messages
Stores real-time chat messages to allow users to revisit their chat history
Retained for a short period of time (or until user clears chat)
Wireframe


Link to wireframe

Project Starting Priorities
Core Instruction
User Authentication
Implement basic Registration and Login with password hashing and JWT(to be discussed) management.
Basic Video Upload and Storage
Create a simple upload API which can save the video and records the metadata in the database.
Video Streaming
Set up a basic video player that can fetch and play the videos from the storage server.
Database Schema Design
Initialize the core schema to support basic CRUD operations.
Essential Function
Search
Implement a basic search bar with keyword matching and related algorithms.
Concurrency Handling
User Dashboard and Profile
Develop the UI for users to update their profile.
Users can view their own uploaded videos.
Advanced Feature
AI Intelligence integration
Integrate the LLM agent for AI-Summarization and automated tagging
Real-time Communication
Implement WebSockets for real-time chat.

LLM Teammate

Name: Bobby

Roles: QA (Testing), Dummy Data Generator, Code reviewer (code conventions, quality, suggestions),, Suggestion Generator, Documentation Specialist

Models: Claude Code, GitHub Copilot
