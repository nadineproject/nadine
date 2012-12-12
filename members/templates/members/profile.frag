<div id="profile">
	<table>
	<tr>
		<td>Membership:</td>
		<td>{{ user.profile.membership_type }}</td>
	</tr>
	<tr>
      <td>Member Since:</td>
      <td>{{ member.first_visit }}</td>
   </tr>
   {% if member.company_name %}
      <tr>
         <td>Company Name</td>
         <td>{{ member.company_name }}</td>
      </tr>
   {% endif %}
   {% if member.url_personal %}
      <tr>
         <td>Personal Website:</td>
         <td><a href="{{ member.url_personal }}">{{ member.url_personal }}</a></td>
      </tr>
   {% endif %}
   {% if member.url_professional %}
      <tr>
         <td>Professional Website:</td>
         <td><a href="{{ member.url_professional }}">{{ member.url_professional }}</a></td>
      </tr>
   {% endif %}
   {% if member.url_facebook %}
      <tr>
         <td>Facebook:</td>
         <td><a href="{{ member.url_facebook }}">{{ member.url_facebook }}</a></td>
      </tr>
   {% endif %}
   {% if member.url_twitter %}
      <tr>
         <td>Twitter:</td>
         <td><a href="{{ member.url_twitter }}">{{ member.url_twitter }}</a></td>
      </tr>
   {% endif %}
   {% if member.url_biznik %}
      <tr>
         <td>Biznik:</td>
         <td><a href="{{ member.url_biznik }}">{{ member.url_biznik }}</a></td>
      </tr>
   {% endif %}
   {% if member.url_linkedin %}
      <tr>
         <td>Linkedin:</td>
         <td><a href="{{ member.url_linkedin }}">{{ member.url_linkedin }}</a></td>
      </tr>
   {% endif %}
   {% if member.url_github %}
      <tr>
         <td>Github:</td>
         <td><a href="{{ member.url_github }}">{{ member.url_github }}</a></td>
      </tr>
   {% endif %}
   {% if member.url_aboutme %}
      <tr>
         <td>About Me:</td>
         <td><a href="{{ member.url_aboutme }}">{{ member.url_aboutme }}</a></td>
      </tr>
   {% endif %}
   {% if member.industry %}
      <tr>
         <td>Industry:</td>
         <td>{{ member.industry }}</td>
      </tr>
   {% endif %}
   {% if member.neighborhood %}
      <tr>
         <td>Neighborhood:</td>
         <td>{{ member.neighborhood }}</td>
      </tr>
   {% endif %}
   {% if member.has_kids %}
      <tr>
         <td>Has Kids?</td>
         <td>{{ member.has_kids }}</td>
      </tr>
   {% endif %} 
	</table>
</div>