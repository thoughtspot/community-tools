const connection_division = document.getElementById('ts_connection_div');
const table_division = document.getElementById('ts_table_div');
const partition_division = document.getElementById('ts_partition_div');
const connection_tab = document.getElementById('btn_connection');
const table_tab = document.getElementById('btn_table');
const partition_tab = document.getElementById('btn_partition');

function main() {
    openTabContent('Connection')
    /*connection_division.style.display = 'Block';
    connection_tab.className = 'active';
    table_division.style.display = 'None';
    table_tab.className = 'inactive';
    partition_division.style.display = 'None';
    partition_tab.className = 'inactive';*/
}

const unhidePartitionTab = () => {
    let createTableFlag = window.Alteryx.Gui.Manager.getDataItem('CreateTable')
    if (createTableFlag.getValue()) {
        partition_tab.disabled = false;
    } else {
        partition_tab.disabled = true;
    }
}
function openTabContent(tabID) {
    // Declare all variables
    let i, tabcontent, tablinks;

    // Get all elements with class="tabcontent" and hide them
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
       tabcontent[i].style.display = "none";
    }

    // Get all elements with class="tablinks" and remove the class "active"
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
       tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    if (tabID == 'Connection') {
        connection_division.style.display = 'Block';
        connection_tab.className = 'active';
        table_division.style.display = 'None';
        table_tab.className = 'inactive';
        partition_division.style.display = 'None';
        partition_tab.className = 'inactive';
    } else if (tabID == 'Table') {
        connection_division.style.display = "None";
        connection_tab.className = 'inactive';
        table_division.style.display = "Block";
        table_tab.className = 'active';
        partition_division.style.display = 'None';
        partition_tab.className = 'inactive';
    } else if (tabID == 'Partition') {
        connection_division.style.display = "None";
        connection_tab.className = 'inactive';
        table_division.style.display = "None";
        table_tab.className = 'inactive';
        partition_division.style.display = 'Block';
        partition_tab.className = 'active';

    } else {
        document.getElementById(tabID).style.display = "block";
    }
    //event.currentTarget.className += " active";
}
