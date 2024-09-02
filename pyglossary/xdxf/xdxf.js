
prepare_tooltips()

// iterate over all tags that can show tooltip
function prepare_tooltips() {
    var pos_elems = document.querySelectorAll(".pos");
    var abbr_elems = document.querySelectorAll(".abbr");
    iterate_over_abbr_elems(pos_elems)
    iterate_over_abbr_elems(abbr_elems)
}

function iterate_over_abbr_elems(elems) {
    for (var i = 0; i < elems.length; i++) {
        var elem = elems[i];
        if (abbr_map.has(elem.textContent)) {
            elem.classList.add("abbr");
            elem.classList.remove("pos");
            elem.addEventListener("mouseover", show_popup);
            elem.addEventListener("mouseout", hide_popup);
        } else {
            elem.classList.add("pos");
            elem.classList.remove("abbr");
        }
    }
}

function show_popup(event) {
    var pos_elem = event.target
    var pos_text = pos_elem.textContent
    var s = document.createElement("small");
    s.classList.add("abbr_popup");
    s.innerHTML = abbr_map.get(pos_text)
    pos_elem.parentNode.insertBefore(s, pos_elem.nextSibling);

    if (s.offsetWidth > 200) {
        if ((pos_elem.offsetLeft + 200) > document.body.offsetWidth) {
            s.style.left = pos_elem.offsetLeft - ((pos_elem.offsetLeft + 200) - document.body.offsetWidth) + 'px';
        } else {
            s.style.left = pos_elem.offsetLeft + 'px';
        }
    } else {
        if ((pos_elem.offsetLeft + s.offsetWidth) > document.body.offsetWidth) {
            s.style.left = pos_elem.offsetLeft - ((pos_elem.offsetLeft + s.offsetWidth) - document.body.offsetWidth) + 'px';
        } else {
            s.style.left = pos_elem.offsetLeft + 'px';
        }
    }
    s.style.display = 'block';
}

function hide_popup(event) {
    var popups = document.getElementsByClassName('abbr_popup');
    for (var i = 0; i < popups.length; ++i) {
        popups[i].remove();
    }
}
