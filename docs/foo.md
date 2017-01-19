Foo
===

This is how to add a toctree with recommonmark AutoStructify transform:

* [Alerts](alerts.md)

Which transforms mostly to:

```eval_rst
.. toctree::
   :maxdepth: 2

   alerts
```

`eval_rst` is a recommonmark piece that lets you drop rST into Markdown, if you
really don't want to author with rST.
