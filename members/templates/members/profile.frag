<div id="profile">
	<table>
	<tr>
		<td>Membership status</td>
		<td>{{ user.profile.membership_type }}</td>
	</tr>
	<tr>
      <td>Member Since</td>
      <td>{{ member.first_visit }}</td>
   </tr>
   {% if member.company_name %}
      <tr>
         <td>Company Name</td>
         <td>{{ member.company_name }}</td>
      </tr>
   {% endif %}
   {% if member.website %}
      <tr>
         <td>Website</td>
         <td><a href="{{ member.website }}">{{ member.website }}</a></td>
      </tr>
   {% endif %}
   {% if member.industry %}
      <tr>
         <td>Industry</td>
         <td>{{ member.industry }}</td>
      </tr>
   {% endif %}
   {% if member.neighborhood %}
      <tr>
         <td>Neighborhood</td>
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