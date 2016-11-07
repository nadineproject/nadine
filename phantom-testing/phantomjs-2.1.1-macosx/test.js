//This test.js currently logs in the user and redirects to user index page

var url = 'http://127.0.0.1:8000/';

var page = new WebPage(), testindex = 0, loadInProgress = false;

page.onConsoleMessage = function(msg) {
  console.log(msg);
};

page.onLoadStarted = function() {
  loadInProgress = true;
  console.log("load started");
};

page.onLoadFinished = function() {
  loadInProgress = false;
  console.log("load finished");
};

var steps = [
  function() {
    page.open(url + 'login');
  },
  function() {
    page.evaluate(function() {
      var form = document.getElementById("login_form");
      var element = form.getAttribute('method');
      if (element == "POST") {
        //insert testing username
        form.elements["username"].value="";
        //insert testing password
        form.elements["password"].value="";
      }
    });
  },
  function() {
    page.evaluate(function() {
      var form = document.getElementById("login_form");
      var element = form.getAttribute('method');
      if (element == "POST") {
        form.submit();
      }
    });
  },
  function() {
    page.render('done.png');
    page.evaluate(function() {
      console.log(document.querySelectorAll('html')[0].outerHTML);
    });
  }
];


interval = setInterval(function() {
  if (!loadInProgress && typeof steps[testindex] == "function") {
    console.log("step " + (testindex + 1));
    steps[testindex]();
    testindex++;
  }
  if (typeof steps[testindex] != "function") {
    console.log("test complete!");
    phantom.exit();
  }
}, 50);
