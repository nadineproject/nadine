var url = 'http://127.0.0.1:8000';

username = casper.cli.get('username');
password = casper.cli.get('password');

casper.on("page.error", function(msg, trace) {
    this.echo("Page Error: " + msg, "ERROR");
});

casper.test.begin('Profile page links working', 3, function suite(test) {
  casper.start(urls + 'member/profile/' + username + '/', function() {
    test.assertTitle("Login | Office Nomads", "Login page title is the one expected");
    test.assertExists('form[method="post"]', "login form is found");
    this.fill("form[method='post']", {
      'username': username,
      'password': password
    }, true);
  });

  casper.then(function() {
    this.log('Logging in', 'debug');
    this.evaluate(function() {
      document.getElementById('loginonly-btn').click();
    });
  });

  casper.run(function() {
    test.done();
  })
})
