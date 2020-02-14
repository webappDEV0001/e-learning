$(document).ready( function () {
    $('#result_list').DataTable( {
        "paging": false,
        "info": false,
        dom: 'Bfrtip',
        buttons : [ {
            extend : 'excel',
            text : 'Export to Excel',
            exportOptions : {
                                columns: 'th:not(:last-child)',
                                modifier : {
                                                // DataTables core
                                                order : 'index', // 'current', 'applied', 'index', 'original'
                                                page : 'none', // 'all', 'current'
                                                search : 'none' // 'none', 'applied', 'removed'
                                            }
                            }
                } ],
        "order": [0, "asc"]
        } );
} );

