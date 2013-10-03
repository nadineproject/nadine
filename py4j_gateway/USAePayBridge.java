import py4j.GatewayServer;
import com.usaepay.api.jaxws.*;
import java.math.BigInteger;
import java.util.*;
import java.lang.reflect.*;

public class USAePayBridge {
	private UeSoapServerPortType client;
	private UeSecurityToken token;

	public USAePayBridge(String url, String key, String pin) throws Exception {
		// Not sure what IP is used for so I'll just stub it out - JLS
		String ip = "";
		client = usaepay.getClient(url);
		token = usaepay.getToken(key, pin, ip);		
	}
	
	public CustomerObject getCustomer(String user_id) throws Exception {
		System.out.println("getCustomer: " + user_id);
		BigInteger customer_number = getCustomerNumber(user_id);
		CustomerObject customer = client.getCustomer(token, customer_number);
		return customer;
	}
	
	public List searchCustomers(String user_id) throws Exception {
		return searchCustomers(user_id, true, 0, 100, "created");
	}
	
	public List searchCustomers(String user_id, boolean match_all, int start, int limit, String sort_by) throws Exception {
		System.out.println("searchCustomers: " + user_id);
		SearchParamArray search = new SearchParamArray();
		search.add(new SearchParam("CustomerID", "eq", user_id));
		CustomerSearchResult result = client.searchCustomers(token, search, match_all, BigInteger.valueOf(start), BigInteger.valueOf(limit), sort_by);
		System.out.println("searchCustomers: found " + result.getCustomersReturned());
		CustomerObjectArray customerArray = result.getCustomers();
		return customerArray.getCustomers();
	}
	
	public void enableCustomer(String user_id) throws Exception {
		System.out.println("enableCustomer: " + user_id);
		BigInteger customer_number = getCustomerNumber(user_id);
		client.enableCustomer(token, customer_number);
	}

	public void disableCustomer(String user_id) throws Exception {
		System.out.println("disableCustomer: " + user_id);
		BigInteger customer_number = getCustomerNumber(user_id);
		disableCustomer(customer_number);
	}
	
	public void disableCustomer(BigInteger customer_number) throws Exception {
		System.out.println("disableCustomer: " + customer_number);
		client.disableCustomer(token, customer_number);
	}

	public void disableAll(String user_id) throws Exception {
		System.out.println("disableAll: " + user_id);
		List customers = searchCustomers(user_id);
		ListIterator it = customers.listIterator();
		while(it.hasNext()){
			CustomerObject customer = (CustomerObject) it.next();
			BigInteger customer_number = BigInteger.valueOf(Long.parseLong(customer.getCustNum()));
			disableCustomer(customer_number);
		}
	}
	
	public BigInteger getCustomerNumber(String user_id) throws Exception {
		BigInteger n = client.searchCustomerID(token, user_id);
		System.out.println("getCustomerNumber: " + user_id + " = " + n);
		return n;
	}

	public static void main(String[] args) {
		String url = args[0];
		String key = args[1];
		String pin = args[2];
		
		try {
			System.out.print("Connecting to " + url + "... ");
			USAePayBridge app = new USAePayBridge(url, key, pin);
			System.out.println("Done");

			System.out.print("Starting Gateway... ");
			GatewayServer server = new GatewayServer(app);
			server.start();
			System.out.println("Done");

			System.out.println("Accepting python connections");
			
			//dump_methods("com.usaepay.api.jaxws.CustomerObject");
		} catch (Exception e) {
			System.out.println("Error!");
			System.out.println(e.getMessage());
		}
	}
	
	public static void dump_methods(String classname) {
		System.out.println("Methods for " + classname);
        try {
            Class c = Class.forName(classname);
            Method m[] = c.getDeclaredMethods();
            for (int i = 0; i < m.length; i++)
            System.out.println(m[i].toString());
        }
        catch (Throwable e) {
            System.err.println(e);
        }
    }

}