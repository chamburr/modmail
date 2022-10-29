<template>
  <div>
    <Heading title="Commands">
      These are the bot commands. Click on them to expand for more information.
    </Heading>
    <div class="row">
      <div class="col-12 col-md-4">
        <Card class="command-tabs" body-classes="py-0">
          <Tab @change="updateCategory">
            <TabPane
              v-for="element in categories"
              :key="element"
              :title="element"
              class="d-block"
            />
          </Tab>
        </Card>
      </div>
      <div class="col-12 col-md-8 mt-4 mt-md-0">
        <BaseInput v-model="search" placeholder="Search..." class="mb-4"></BaseInput>
        <div v-if="activeCommands.length !== 0">
          <Card
            v-for="(element, index) in activeCommands"
            :key="element.name"
            class="commands-card mb-4"
            body-classes="py-0"
            header-classes="border-0 p-0"
          >
            <template #header>
              <div v-b-toggle="`commands-${index}`" class="px-4 py-3">
                <span class="font-weight-bolder">
                  {{ prefix }}{{ element.name }} {{ element.usage }}
                </span>
                <span class="float-right text-light">{{ getParent(element.name) }}</span>
              </div>
            </template>
            <BCollapse :id="`commands-${index}`" role="tabpanel">
              <div class="mb-3">
                <p class="mb-0">{{ element.description }}</p>
                <p v-if="element.alias" class="mt-2 mb-0 text-light">
                  Aliases: {{ element.alias }}
                </p>
                <p v-if="element.permission" class="mt-2 mb-0 text-light">
                  Permissions: {{ element.permission }}
                </p>
              </div>
            </BCollapse>
          </Card>
        </div>
        <div v-else class="text-center mt-4">
          <span class="display-2">:(</span>
          <p class="h5 mt-4">No results found.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  async asyncData({ $getContent }) {
    return {
      commands: await $getContent('commands'),
    }
  },
  data() {
    return {
      search: '',
      category: 'All',
      prefix: this.$route.query.prefix || '=',
    }
  },
  head: {
    title: 'Commands',
  },
  computed: {
    categories() {
      return [
        'All',
        ...this.commands.filter(element => !element.description).map(element => element.name),
      ]
    },
    activeCommands() {
      return this.commands.filter(element => {
        return (
          element.description &&
          (this.category === 'All' || this.category === this.getParent(element.name)) &&
          (element.name.includes(this.search) ||
            (element.alias && element.alias.includes(this.search)))
        )
      })
    },
  },
  methods: {
    getParent(name) {
      return this.commands
        .slice(
          0,
          this.commands.findIndex(element => element.name === name)
        )
        .reverse()
        .find(element => !element.description).name
    },
    updateCategory(tabs, index) {
      this.category = tabs[index].title
    },
  },
}
</script>

<style scoped lang="scss">
.command-tabs {
  position: sticky;
  top: calc(76px + 2em);

  ::v-deep .active {
    background-color: $primary !important;
  }

  ::v-deep a {
    padding-top: 6px;
    padding-bottom: 6px;
    background-color: $gray-700 !important;
  }

  ::v-deep li {
    padding-right: 0 !important;
    margin-bottom: 0.5em;
    margin-top: 0.5em;
    display: block;
  }

  ::v-deep ul {
    flex-direction: column;
  }

  ::v-deep a > div {
    color: white !important;
    font-weight: 600;
  }
}

.commands-card {
  ::v-deep div:focus {
    outline: none;
  }
}
</style>
