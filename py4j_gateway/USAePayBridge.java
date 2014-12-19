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

	public List getTransactions(String year, String month, String day) throws Exception {
		String[] dates = getDateRange(year, month, day);
		String start = dates[0];
		String end = dates[1];
		System.out.println("getTransactions: " + start);
		SearchParamArray search = new SearchParamArray();
		search.add(new SearchParam("created", "gte", start));
		search.add(new SearchParam("created", "lte", end));
		return searchTransactions(search);
	}

	public List searchTransactions(SearchParamArray search) throws Exception {
		return searchTransactions(search, true, 0, 100, "created");
	}
	
	public List searchTransactions(SearchParamArray search, boolean match_all, int start, int limit, String sort_by) throws Exception {
		TransactionSearchResult result = client.searchTransactions(token, search, match_all, BigInteger.valueOf(start), BigInteger.valueOf(limit), sort_by);
		System.out.println("searchTransactions: found " + result.getTransactionsReturned());
		TransactionObjectArray transactionArray = result.getTransactions();
		return transactionArray.getTransactions();
	}
	
	public List getBatches(String year, String month, String day) throws Exception {
		String[] dates = getDateRange(year, month, day);
		String start = dates[0];
		String end = dates[1];
		System.out.println("getBatches: " + start);
		SearchParamArray search = new SearchParamArray();
		search.add(new SearchParam("opened", "gte", start));
		search.add(new SearchParam("opened", "lte", end));
		return searchBatches(search);
	}

	public List searchBatches(SearchParamArray search) throws Exception {
		return searchBatches(search, true, 0, 100, "opened");
	}
	
	public List searchBatches(SearchParamArray search, boolean match_all, int start, int limit, String sort_by) throws Exception {
		BatchSearchResult result = client.searchBatches(token, search, match_all, BigInteger.valueOf(start), BigInteger.valueOf(limit), sort_by);
		System.out.println("searchBatches: found " + result.getBatchesReturned());
		BatchStatusArray batchArray = result.getBatches();
		return batchArray.getBatchStatuses();
	}
	
	public CustomerObject getCustomer(String user_id) throws Exception {
		System.out.println("getCustomer: " + user_id);
		BigInteger customer_number = getCustomerNumber(user_id);
		CustomerObject customer = client.getCustomer(token, customer_number);
		return customer;
	}
	
	public List getAllCustomers(String user_id) throws Exception {
		System.out.println("getAllCustomers: " + user_id);
		SearchParamArray search = new SearchParamArray();
		search.add(new SearchParam("CustomerID", "eq", user_id));
		return searchCustomers(search);
	}

	public List getEnabledCustomers() throws Exception {
		System.out.println("getEnabledCustomers");
		SearchParamArray search = new SearchParamArray();
		search.add(new SearchParam("Enabled", "eq", "True"));
		return searchCustomers(search, true, 0, 500, "next");
	}
	
	public List searchCustomers(SearchParamArray search) throws Exception {
		return searchCustomers(search, true, 0, 100, "created");
	}
	
	public List searchCustomers(SearchParamArray search, boolean match_all, int start, int limit, String sort_by) throws Exception {
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
		List customers = getAllCustomers(user_id);
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
	
	private String[] getDateRange(String year, String month, String day) {
		// TODO - Add Validation
		String start = year + "-" + month + "-" + day + " 00:00:00";
		String end = year + "-" + month + "-" + day + " 23:59:59";
		String[] dates = {start, end};
		return dates;
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
}