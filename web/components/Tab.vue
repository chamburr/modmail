<template>
  <div>
    <div class="nav-tabs-navigation">
      <div class="nav-tabs-wrapper">
        <div class="nav-wrapper">
          <ul class="nav nav-tabs border-0 nav-fill" role="tablist">
            <li v-for="tab in tabs" :key="tab.title" class="nav-item">
              <a
                data-toggle="tab"
                role="tab"
                class="nav-link border-0 rounded"
                :aria-selected="tab.active"
                :class="{ active: tab.active }"
                @click.prevent="activateTab(tab)"
              >
                <div>
                  {{ tab.title }}
                </div>
              </a>
            </li>
          </ul>
        </div>
      </div>
    </div>
    <div>
      <div slot="content" class="tab-content">
        <slot v-bind="slotData"></slot>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Tab',
  provide() {
    return {
      addTab: this.addTab,
      removeTab: this.removeTab,
    }
  },
  data() {
    return {
      tabs: [],
      activeTabIndex: 0,
    }
  },
  computed: {
    slotData() {
      return {
        activeTabIndex: this.activeTabIndex,
        tabs: this.tabs,
      }
    },
  },
  watch: {
    value(newValue) {
      this.findAndActivateTab(newValue)
    },
  },
  mounted() {
    this.$nextTick(() => {
      if (this.value) {
        this.findAndActivateTab(this.value)
      } else if (this.tabs.length > 0) {
        this.activateTab(this.tabs[0])
      }
    })
  },
  methods: {
    findAndActivateTab(title) {
      const tab = this.tabs.find(tab => tab.title === title)
      if (tab) {
        this.activateTab(tab)
      }
    },
    activateTab(tab) {
      if (this.handleClick) {
        this.handleClick(tab)
      }
      this.deactivateTabs()
      tab.active = true
      this.activeTabIndex = this.tabs.findIndex(t => t.active)
      this.$emit('change', this.tabs, this.activeTabIndex)
    },
    deactivateTabs() {
      this.tabs.forEach(tab => {
        tab.active = false
      })
    },
    addTab(tab) {
      if (this.activeTab === tab.name) {
        tab.active = true
      }
      this.tabs.push(tab)
    },
    removeTab(tab) {
      const index = this.tabs.indexOf(tab)
      if (index > -1) {
        this.tabs.splice(index, 1)
      }
    },
  },
}
</script>
