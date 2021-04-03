<template>
  <BaseNav
    id="header-nav"
    ref="navbar"
    type="dark"
    class="py-3 sticky-top"
    :class="{
      'header-dashboard': dashboard,
      'bg-transparent': transparent,
      'border-bottom': transparent,
    }"
    expand
  >
    <template #brand>
      <NuxtLink class="navbar-brand" to="/">
        <div class="d-flex align-items-center">
          <img
            id="header-icon"
            class="ml-2 mr-3"
            :class="{ 'd-none': dashboard, 'd-md-block': dashboard }"
            src="~/static/icon.png"
            alt="Icon"
          />
          <span class="h4 font-weight-bold mb-0 text-capitalize">Wyvor</span>
        </div>
      </NuxtLink>
    </template>
    <template v-if="dashboard" #container-after>
      <div id="header-user">
        <BaseDropdown position="right" menu-classes="mt-3 border border-light">
          <div slot="title" class="dropdown-toggle dropdown-toggle-no-caret">
            <span id="header-username" class="nav-link font-weight-bolder d-none d-lg-inline">
              {{ $discord.getName(user) }}
            </span>
            <img
              id="header-avatar"
              class="rounded-circle"
              :src="$discord.getAvatar(user)"
              alt="Icon"
            />
          </div>
          <div class="text-center font-weight-bold text-white pb-2 mb-2 border-bottom border-light">
            Actions
          </div>
          <NuxtLink class="dropdown-item font-weight-bold" to="/dashboard">
            <BaseIcon name="fas server" class="pl-0 small" />
            Servers
          </NuxtLink>
          <NuxtLink class="dropdown-item font-weight-bold" to="/users/@me">
            <BaseIcon name="fas user-circle" class="pl-0 small" />
            Profile
          </NuxtLink>
          <NuxtLink class="dropdown-item font-weight-bold" to="/logout">
            <BaseIcon name="fas sign-out-alt" class="pl-0 small" />
            Logout
          </NuxtLink>
        </BaseDropdown>
      </div>
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
        <a
          class="nav-link d-block font-weight-bolder py-2 mr-1"
          target="_blank"
          href="/invite"
          @click.native="closeMenu"
        >
          <span>Invite</span>
        </a>
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
    <ul v-if="!dashboard" class="navbar-nav ml-auto mt-3 mt-lg-0">
      <li>
        <NuxtLink to="/dashboard" @click.native="closeMenu">
          <BaseButton type="primary">Dashboard</BaseButton>
        </NuxtLink>
      </li>
    </ul>
  </BaseNav>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'TheHeader',
  props: {
    dashboard: {
      type: Boolean,
      default: false,
    },
    transparent: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    ...mapGetters('user', ['user']),
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

#header-avatar {
  height: 40px;
}

.navbar-nav .nav-link,
#header-username {
  font-weight: 600;
  font-size: 16px;
  color: white !important;
}

#header-username {
  vertical-align: middle;
}

.navbar-nav .nav-link > span {
  vertical-align: middle;
}

.navbar-nav .nav-link:hover,
#header-username:hover {
  color: $gray-400 !important;
}

.header-dashboard {
  /deep/ .navbar-toggler {
    order: 1;
  }

  /deep/ .navbar-brand {
    order: 2;
  }

  /deep/ #header-user {
    order: 3;
  }

  @include media-breakpoint-down(md) {
    /deep/ .navbar-collapse {
      width: 100%;
      margin: 0;
      max-height: 0;
      transition: max-height 0.2s;
      animation: none;
      overflow: hidden;
    }

    /deep/ .navbar-collapse.show {
      opacity: 1;
      padding-top: 1em !important;
      max-height: 500px;
      transition: max-height 0.2s;
    }
  }
}

@include media-breakpoint-up(lg) {
  .header-dashboard {
    /deep/ .navbar-brand {
      order: 1;
    }

    /deep/ .navbar-collapse {
      order: 2;
    }
  }
}

#header-nav {
  height: 75px;
  background-color: $gray-900;
  z-index: 1000;

  /deep/ .navbar-collapse {
    display: block;
    background-color: $dark;
    top: 75px;
  }

  @include media-breakpoint-down(md) {
    /deep/ .navbar-collapse:not(.show) {
      pointer-events: none;
    }
  }
}

#header-nav.bg-transparent {
  @include media-breakpoint-up(lg) {
    /deep/ .navbar-collapse {
      background-color: transparent !important;
    }
  }
}
</style>
