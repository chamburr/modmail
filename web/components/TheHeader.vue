<template>
  <BaseNav
    id="header-nav"
    ref="navbar"
    type="dark"
    class="py-3 sticky-top"
    :class="{
      'bg-transparent': transparent,
      'border-bottom': transparent,
    }"
    expand
  >
    <template #brand>
      <NuxtLink class="navbar-brand" to="/">
        <div class="d-flex align-items-center">
          <img id="header-icon" class="ml-2 mr-3" src="~/static/icon.png" alt="Icon" />
          <span class="h4 font-weight-bold mb-0 text-capitalize">ModMail</span>
        </div>
      </NuxtLink>
    </template>
    <ul class="navbar-nav align-items-lg-center">
      <li>
        <NuxtLink
          class="nav-link d-block font-weight-bolder py-2 mr-1"
          to="/"
          @click.native="closeMenu"
        >
          <span>Home</span>
        </NuxtLink>
      </li>
      <li>
        <NuxtLink
          class="nav-link d-block font-weight-bolder py-2 mr-1"
          to="/commands"
          @click.native="closeMenu"
        >
          <span>Commands</span>
        </NuxtLink>
      </li>
      <li>
        <NuxtLink
          class="nav-link d-block font-weight-bolder py-2 mr-1"
          to="/faq"
          @click.native="closeMenu"
        >
          <span>FAQ</span>
        </NuxtLink>
      </li>
      <li>
        <NuxtLink
          class="nav-link d-block font-weight-bolder py-2 mr-1"
          to="/premium"
          @click.native="closeMenu"
        >
          <span>Premium</span>
        </NuxtLink>
      </li>
      <li>
        <a
          class="nav-link d-block font-weight-bolder py-2 mr-1"
          target="_blank"
          href="/support"
          @click="closeMenu"
        >
          <span>Support</span>
        </a>
      </li>
    </ul>
    <ul class="navbar-nav ml-auto mt-3 mt-lg-0">
      <li>
        <a target="_blank" href="/invite" @click="closeMenu">
          <BaseButton type="primary">Add to Discord</BaseButton>
        </a>
      </li>
    </ul>
  </BaseNav>
</template>

<script>
export default {
  name: 'TheHeader',
  props: {
    transparent: {
      type: Boolean,
      default: false,
    },
  },
  watch: {
    $route() {
      this.closeMenu()
    },
  },
  methods: {
    closeMenu() {
      if (this.$refs.navbar) {
        this.$refs.navbar.closeMenu()
      }
    },
  },
}
</script>

<style scoped lang="scss">
#header-icon {
  height: 40px;
}

.navbar-nav .nav-link {
  font-weight: 600;
  font-size: 16px;
  color: white !important;
}

.navbar-nav .nav-link > span {
  vertical-align: middle;
}

#header-nav {
  height: 75px;
  background-color: $gray-900;
  z-index: 1000;

  ::v-deep .navbar-collapse {
    display: block;
    background-color: $dark;
    top: 75px;
  }

  @include media-breakpoint-down(md) {
    ::v-deep .navbar-collapse:not(.show) {
      pointer-events: none;
    }
  }
}

#header-nav.bg-transparent {
  @include media-breakpoint-up(lg) {
    ::v-deep .navbar-collapse {
      background-color: transparent !important;
    }
  }
}
</style>
