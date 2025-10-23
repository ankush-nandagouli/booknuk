/* login drop down script */
    function toggleDropdown() {
      document.getElementById("loginDropdown").classList.toggle("hidden");
    }

    function toggleMobileMenu() {
      var menu = document.getElementById("mobileMenu");
      if (menu.classList.contains("hidden")) {
        menu.classList.remove("hidden");
        setTimeout(() => {
          menu.style.maxHeight = "500px";
        }, 10);
      } else {
        menu.style.maxHeight = "0px";
        setTimeout(() => {
          menu.classList.add("hidden");
        }, 300);
      }
    }
/*-------------------------------------------------------------------------------------------*/

/*lazy loading */
    document.addEventListener("DOMContentLoaded", function () {
      const landingSection = document.querySelector("#landing-video-section");
      const navbar = document.querySelector("nav");

      setTimeout(() => {
        landingSection.style.transition = "opacity 1s ease-out";
        landingSection.style.opacity = 0;

        setTimeout(() => {
          landingSection.style.display = "none";
          navbar.scrollIntoView({ behavior: "smooth" });
        }, 1000);
      }, 2000);
    });

/*-------------------------------------------------------------------------*/

/*browse books page search bar script*/
    let timeout = null;
    document.getElementById('searchInput').addEventListener('input', function () {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        document.getElementById('searchForm').submit();
      }, 10000);
    });
    document.getElementById('categorySelect').addEventListener('change', function () {
      document.getElementById('searchForm').submit();
    });

/*---------------------------------------------------------------------*/



/*----------------------------------------------------------------------------------------*/


/*--------------------------------------------------------------------------------------------*/