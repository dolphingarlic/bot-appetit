To get the menu items (ignoring dorms) in JS:

```js
document
    .getElementById("brunch")
    .getElementsByClassName("site-panel__daypart-item");
```

To factor in dorms, maybe do something like:

```js
l = document
    .getElementById("brunch")
    .getElementsByClassName("c-tab__content--active")[0]
    .getElementsByClassName("c-tab__content-inner site-panel__daypart-tab-content-inner")[0]
    .children;

for (let i of l) {
    if (i.tagName.toUpperCase() === "DIV" && i.className === "station-title-inline-block") {
        // Start of new dorm
    }
}
```
