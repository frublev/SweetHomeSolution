
function radio_check(elbyname) {
  let elements = document.getElementsByName(elbyname);
  let disabled_elements = document.getElementsByName('dis');
  for (let i = 0; i < elements.length; i++) {
    let lab = 'check_' + elements[i].id + '';
    if (elements[i].value == "True") {
      elements[i].checked = true;
      document.getElementById(lab).innerText = 'On';
      if (elbyname == 'area_auto') {
        for (let i = 0; i < disabled_elements.length; i++) {
            disabled_elements[i].disabled = true;
        }
      }
    }
    else {
      elements[i].checked = false;
      document.getElementById(lab).innerText = 'Off';
      if (elbyname == 'area_status') {
        for (let i = 0; i < disabled_elements.length; i++) {
            disabled_elements[i].disabled = true;
        }
        let ar_id = elements[i].id;
        ar_id = ar_id.indexOf('off');
        ar_id = ar_id + 3;
        ar_id = elements[i].id.slice(ar_id)
        let el_id = 'area_auto' + ar_id
        document.getElementById(el_id).disabled = true
      }
    }
  }
}

const area_status = async (area_ = '', radio = '') => {
  let url = '/irrigation/' + area_ + '/';
  let area_id = 'area_' + radio + area_;
  let status = document.getElementById(area_id).value;
  let lab_ = 'check_area_' + radio + area_;
  let disabled_ = document.getElementsByName('dis');
  let data = {}

  if (status == "True") {
    data[radio] = false;
  }
  else if (status == "False") {
    data[radio] = true;
  }
  else {
    data[radio] = status;
  }

  if (radio == "schedule") {
    data[radio] = [Number(status) * 1800];
    alert(data[radio])
  }

  if (radio == "duration") {
    data[radio] = [Number(status) * 30];
    alert(data[radio])
  }

  const response = await fetch(url, {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  });
  let area_status = await response.json();
  let el_id_ = 'area_auto' + area_;
  if (typeof area_status[radio] == "boolean" && area_status[radio] == true) {
    document.getElementById(area_id).value = "True";
    document.getElementById(lab_).innerText = "On";
    if (radio == 'on_off') {
        if (document.getElementById(el_id_).value != "True") {
            for (let i = 0; i < disabled_.length; i++) {
                disabled_[i].disabled = false;
            }
        }
        document.getElementById(el_id_).disabled = false;
    }
    if (radio == 'auto'){
        for (let i = 0; i < disabled_.length; i++) {
            disabled_[i].disabled = true;
        }
    }

  }
  else if (typeof area_status[radio] == "boolean" && area_status[radio] == false) {
    document.getElementById(area_id).value = "False";
    document.getElementById(lab_).innerText = "Off";
    if (radio == 'on_off') {
        document.getElementById(el_id_).disabled = true;
        for (let i = 0; i < disabled_.length; i++) {
            disabled_[i].disabled = true;
        }
    }
    if (radio == 'auto'){
        for (let i = 0; i < disabled_.length; i++) {
            disabled_[i].disabled = false;
        }
    }
  }
  return;
}
