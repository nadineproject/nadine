<div id="profile">
	<table>
	<tr>
		<td>Membership:</td>
		<td>{{ user.profile.membership_type }}</td>
	</tr>
	<tr>
      <td>Member Since:</td>
      <td>{{ user.profile.first_visit }}</td>
   </tr>
   {% if user.profile.company_name %}
      <tr>
         <td>Company Name</td>
         <td>{{ user.profile.company_name }}</td>
      </tr>
   {% endif %}
   {% if user.profile.url_personal %}
      <tr>
         <td>Personal Website:</td>
         <td><a target="_self" href="{{ user.profile.url_personal }}">{{ user.profile.url_personal }}</a></td>
      </tr>
   {% endif %}
   {% if user.profile.url_professional %}
      <tr>
         <td>Professional Website:</td>
         <td><a target="_self" href="{{ user.profile.url_professional }}">{{ user.profile.url_professional }}</a></td>
      </tr>
   {% endif %}
   {% if user.profile.url_facebook %}
      <tr>
         <td>Facebook:</td>
         <td><a target="_self" href="{{ user.profile.url_facebook }}">{{ user.profile.url_facebook }}</a></td>
      </tr>
   {% endif %}
   {% if user.profile.url_twitter %}
      <tr>
         <td>Twitter:</td>
         <td><a target="_self" href="{{ user.profile.url_twitter }}">{{ user.profile.url_twitter }}</a></td>
      </tr>
   {% endif %}

   {% if user.profile.url_linkedin %}
      <tr>
         <td>Linkedin:</td>
         <td><a target="_self" href="{{ user.profile.url_linkedin }}">{{ user.profile.url_linkedin }}</a></td>
      </tr>
   {% endif %}
   {% if user.profile.url_github %}
      <tr>
         <td>Github:</td>
         <td><a target="_self" href="{{ user.profile.url_github }}">{{ user.profile.url_github }}</a></td>
      </tr>
   {% endif %}
   {% if user.profile.url_aboutme %}
      <tr>
         <td>About Me:</td>
         <td><a target="_self" href="{{ user.profile.url_aboutme }}">{{ user.profile.url_aboutme }}</a></td>
      </tr>
   {% endif %}
   {% if user.profile.industry %}
      <tr>
         <td>Industry:</td>
         <td>{{ user.profile.industry }}</td>
      </tr>
   {% endif %}
   {% if user.profile.neighborhood %}
      <tr>
         <td>Neighborhood:</td>
         <td>{{ user.profile.neighborhood }}</td>
      </tr>
   {% endif %}
   {% if user.profile.has_kids %}
      <tr>
         <td>Has Kids?</td>
         <td>{{ user.profile.has_kids }}</td>
      </tr>
   {% endif %}
	</table>
</div>
