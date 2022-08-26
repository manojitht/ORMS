const home_body = document.querySelector(".home-body"),
      sidebar = document.querySelector(".home-sidebar"),
      toggle = document.querySelector(".toggle"),
      search_button = document.querySelector(".search-box");

      toggle.addEventListener("click", () => {
          sidebar.classList.toggle("close")
      });

      search_button.addEventListener("click", () => {
        sidebar.classList.remove("close")
      });

    $(document).ready(function () {
      $('#team_requests').DataTable();
     });

    function toggle_blur(){
      var blur = document.getElementById('blur');
      blur.classList.toggle('active');
    
      var request_popup = document.getElementById('request_popup');
      request_popup.classList.toggle('active');
  }
