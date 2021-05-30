<template>
  <div>
    <Heading title="Premium">
      Get ModMail Premium to upgrade your server experience and support the development work!
    </Heading>
    <div class="row text-center justify-content-around">
      <div v-for="(element, index) in premium" :key="index" class="col-12 col-md-4 px-2 mb-4">
        <Card
          class="bg-transparent shadow-none border-0"
          body-classes="pt-2"
          header-classes="border-0 p-0"
        >
          <template #header>
            <span class="h5 font-weight-bold">{{ element.name }}</span>
          </template>
          {{ element.description }}
        </Card>
      </div>
    </div>
    <div class="row mt-4 text-center justify-content-around">
      <div class="col-lg-1"></div>
      <div class="col-12 col-md-4 col-lg-3 mb-4 px-2 my-md-auto">
        <CardPremium
          name="Basic"
          role="Patrons"
          color="#ffd700"
          :price="30"
          :server="1"
          @click="loadPremium('basic')"
        />
      </div>
      <div class="col-12 col-md-4 col-lg-3 mb-4 px-2 my-md-auto">
        <CardPremium
          name="Pro"
          role="Super Patrons"
          color="#ffa500"
          :price="60"
          :server="3"
          :popular="true"
          @click="loadPremium('pro')"
        />
      </div>
      <div class="col-12 col-md-4 col-lg-3 mb-4 px-2 my-md-auto">
        <CardPremium
          name="Plus"
          role="Super Duper Patrons"
          color="#ff4500"
          :price="90"
          :server="5"
          @click="loadPremium('plus')"
        />
      </div>
      <div class="col-lg-1"></div>
    </div>
    <div class="text-left mt-5 pt-4">
      <p class="h5">Need Something Professional?</p>
      <p>
        We can host an exclusive instance just for your server! This include the premium features
        listed above, and you will also get to customise the bot username, avatar and status. Please
        contact James [a_leon]#6196 on Discord for more information.
      </p>
    </div>
  </div>
</template>

<script>
export default {
  async asyncData({ $getContent }) {
    return {
      premium: await $getContent('premium'),
    }
  },
  head: {
    title: 'Premium',
  },
  async mounted() {
    await this.loadPremium()
  },
  methods: {
    async loadPremium(plan) {
      if (plan) {
        await this.$router.push({ path: this.$route.path, query: { plan } })
      } else if (this.$route.query.plan) {
        plan = this.$route.query.plan.toLowerCase()
      } else {
        return
      }

      if (plan === 'basic') {
        await this.showPremium('Basic', 30, 1)
      } else if (plan === 'pro') {
        await this.showPremium('Pro', 60, 3)
      } else if (plan === 'plus') {
        await this.showPremium('Plus', 90, 5)
      }
    },
    async showPremium(name, price, server) {
      if (this.$store.getters['user/isNull']) {
        const user = await this.$axios.$get('/users/@me').catch(async err => {
          if (err.response.status !== 401) this.$fatal(err)
          else
            await this.$router.push(`/login?redirect=${encodeURIComponent(this.$route.fullPath)}`)
        })

        if (!user) return

        this.$store.commit('user/set', user)
      }

      const user = this.$store.getters['user/get']
      const username = user.username.replace(/</g, '&lt;').replace(/>/g, '&gt;')
      const message = this.$createElement('div', {
        domProps: {
          innerHTML: `
            <p class="font-weight-bold mb-2">${name} Plan (${server} servers)</p>
            <p class="mb-4">
              Before proceeeding to payment, please join our
              <a target="_blank" href="/support">support server</a> to receive the role and rewards.
            </p>
            <p class="mb-0">
              Signed in as ${username}#${user.discriminator}.
              <a href="/logout">Not you?</a>
            </p>
            <form id="premium-form" action="https://www.paypal.com/cgi-bin/webscr" method="post"
                target="_top" novalidate>
              <input type="hidden" name="business" value="redfreebird41@gmail.com">
              <input type="hidden" name="lc" value="en_US">
              <input type="hidden" name="cmd" value="_xclick">
              <input type="hidden" name="amount" value="${price}.00">
              <input type="hidden" name="item_name" value="ModMail Premium (${name})">
              <input type="hidden" name="no_shipping" value="1">
              <input type="hidden" name="currency_code" value="USD">
              <input type="hidden" name="custom" value="${user.id}">
              <input type="hidden" name="notify_url" value="https://modmail.xyz/api/webhooks/payment">
              <input type="hidden" name="return" value="https://modmail.xyz/success">
              <input type="hidden" name="cancel_return" value="https://modmail.xyz/premium">
            </form>
          `,
        },
      })

      await this.$modal([message], {
        title: 'ModMail Premium',
        okTitle: 'Continue with PayPal',
        footerClass: 'test',
        cancelVariant: 'gray d-none',
      }).then(async res => {
        if (!res) {
          await this.$router.push({ path: this.$route.path })
          return
        }
        document.getElementById('premium-form').submit()
      })
    },
  },
}
</script>
