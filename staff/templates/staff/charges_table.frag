<h3>{{ name }} Sales</h3>
<table>
    <tr class="row-even">
        <th>Member</th>
        <th>Description</th>
        <!--<th>Type</th>-->
        <th>Status</th>
        <th>Charge</th>
        <th>Bill</th>
        <th>Invoice</th>
        <th>Action</th>
    </tr>

    {% for t in transactions %}
        <tr>
            <td><a href="{% url 'staff.views.member_detail_user' t.username %}">{{ t.username }}</a></td>
            <td>{{ t.description }}</td>
            <!--<td>{{ t.card_type }}</td>-->
            <td>{{ t.status}}</td>
            <td {% if t.open_bill_amount and t.open_bill_amount != t.amount %} style="color:red;" {% endif %}>
                {{ t.amount|floatformat:2 }}
            </td>
            <td>
                {% if t.open_bill_amount %} ${{ t.open_bill_amount|floatformat:2 }} {% endif %}
            </td>
            <td>
                {% for i in t.xero_invoices %}
                    <a href="https://go.xero.com/AccountsReceivable/View.aspx?InvoiceID={{ i.InvoiceID }}" target="_new">{{ i.InvoiceNumber }}</a>
                {% endfor %}
            </td>
            <td style="text-align:center;">
                {% if t.open_bill_amount %}
                    <form action="{% url 'staff.views.bills_pay_all' t.username %}" method="POST">
                        <input type="hidden" name="next" value="{{request.path}}" />
                        <input type="submit" value="Paid" />
                        {% csrf_token %}
                    </form>
                {% endif %}
            </td>
        </tr>
    {% endfor %}
    
    <tr class="row-even">
        <td colspan="3" style="text-align:right;"><strong>{{ transactions|length }} {{ name }} Transactions</strong></td>
        <td>${{total|floatformat:2}}</td>
        <td colspan="3"></td>
    </tr>
</table>