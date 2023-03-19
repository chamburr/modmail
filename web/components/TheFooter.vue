<template>
  <div id="footer-container" class="pt-5 pb-4">
    <nav class="navbar bg-transparent">
      <div class="container">
        <div class="row">
          <div class="col-12 col-md-5 mb-2">
            <img id="footer-icon" class="mb-2 mr-2" src="~/static/icon.png" alt="Icon" />
            <p class="d-inline display-4">ModMail</p>
            <p class="mt-3">
              A feature-rich Discord bot for easy communication between server staff and users.
            </p>
            <p class="mb-0">
              Copyright © 2019-2023
              <a class="footer-link" target="_blank" rel="noopener" href="https://chamburr.com">
                CHamburr
              </a>
            </p>
          </div>
          <div class="col-md-1 mb-2"></div>
          <div class="col-12 col-md-6 mb-2">
            <div class="row">
              <div class="col-6 col-md-4 mb-2">
                <p class="font-weight-bolder mb-2">Product</p>
                <NuxtLink class="footer-link d-block" to="/">Home</NuxtLink>
                <NuxtLink class="footer-link d-block" to="/commands">Commands</NuxtLink>
                <NuxtLink class="footer-link d-block" to="/faq">FAQ</NuxtLink>
                <NuxtLink class="footer-link d-block" to="/premium">Premium</NuxtLink>
                <a class="footer-link d-block" target="_blank" href="/invite">Invite</a>
              </div>
              <div class="col-6 col-md-4 mb-2">
                <p class="font-weight-bolder mb-2">&#8203;</p>
                <a class="footer-link d-block" target="_blank" href="/support">Support</a>
                <a class="footer-link d-block" target="_blank" href="/github">GitHub</a>
                <NuxtLink class="footer-link d-block" to="/partners">Partners</NuxtLink>
                <NuxtLink class="footer-link d-block" to="/status">Status</NuxtLink>
              </div>
              <div class="col-6 col-md-4 mb-2">
                <p class="font-weight-bolder mb-2">Legal</p>
                <NuxtLink class="footer-link d-block" to="/about">About Us</NuxtLink>
                <NuxtLink class="footer-link d-block" to="/terms">Terms</NuxtLink>
                <NuxtLink class="footer-link d-block" to="/privacy">Privacy</NuxtLink>
                <a class="footer-link d-block" target="_blank" href="mailto:hi@modmail.xyz">
                  Contact
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>
  </div>
</template>

<script>
export default {
  name: 'TheFooter',
}
</script>

<style scoped lang="scss">
#footer-icon {
  width: 40px;
  height: 40px;
}

.footer-link {
  color: white !important;
  line-height: 30px;
}

.footer-link:hover {
  color: white !important;
  text-decoration: underline;
}

#footer-container {
  background-color: $gray-900 !important;
}
</style>
