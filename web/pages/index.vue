<template>
  <div>
    <div id="hero-top-container">
      <div id="hero-top-pattern">
        <img id="hero-top-pattern-inner" src="~/assets/images/pattern.svg" alt="Splash" />
      </div>
      <div id="hero-top-content" class="container pt-2 pb-0">
        <div class="row h-100">
          <div class="hero-top-column col-12 col-md-7 text-center text-md-left">
            <div class="d-md-none text-center mt-5 mb-3">
              <img id="hero-top-icon-sm" src="~/static/icon.png" alt="Icon" />
            </div>
            <h1 class="display-1">
              <span class="d-none d-md-inline font-weight-bold">Meet</span>
              ModMail<span class="d-none d-md-inline font-weight-bold">.</span>
            </h1>
            <h2 class="display-4">
              The best feature-rich Discord music bot.
              <br class="d-none d-lg-block" />
              Take control over your music with an intuitive dashboard, custom effects and more!
            </h2>
            <div class="d-inline-block">
              <a target="_blank" href="/invite" class="mx-2 ml-md-0">
                <BaseButton type="primary" size="lg" class="mt-3">
                  <span class="h6 font-weight-bold">Add to Discord</span>
                </BaseButton>
              </a>
              <a target="_blank" href="/github" class="mx-2 ml-md-0">
                <BaseButton type="primary" size="lg" class="mt-3">
                  <span class="h6 font-weight-bold">GitHub</span>
                </BaseButton>
              </a>
            </div>
          </div>
          <div class="hero-top-column col-md-5 d-none d-md-flex align-items-center">
            <img id="hero-top-icon" src="~/static/icon.png" alt="Icon" />
          </div>
        </div>
      </div>
      <img id="hero-top-wave" src="~/assets/images/hero-1.svg" alt="Hero" />
    </div>
    <div class="container text-center pb-5">
      <h2 class="display-2 mt-5 pb-3">About ModMail</h2>
      <p>
        ModMail is a feature-rich Discord bot designed to enable your server members to contact
        staff easily. A new channel is created whenever a user messages the bot, and the channel
        will serve as a shared inbox for seamless communication between staff and the user.
      </p>
      <h2 class="display-2 mt-5 pb-3">Features</h2>
      <div
        v-for="(element, index) in features"
        :key="element.name"
        class="home-feature-container row pb-5 d-flex flex-md-row"
        :class="{ 'flex-column-reverse': index % 2 === 0 }"
      >
        <div
          v-if="index % 2 === 1"
          class="home-feature-column feature-icon col-12 col-md-6 align-items-center"
        >
          <img class="home-feature-image" :src="images[index]" alt="Icon" />
        </div>
        <div class="home-feature-column feature-text col-12 col-md-6 mt-4 mt-md-0">
          <h3 class="display-4">
            {{ element.name }}
          </h3>
          <p>
            {{ element.description }}
          </p>
        </div>
        <div
          v-if="index % 2 === 0"
          class="home-feature-column feature-icon col-12 col-md-6 align-items-center"
        >
          <img class="home-feature-image" :src="images[index]" alt="Icon" />
        </div>
      </div>
    </div>
    <div id="hero-bottom-container">
      <img id="hero-bottom-wave" src="~/assets/images/hero-2.svg" alt="Hero" />
      <div class="container text-center px-5 pb-5 pt-4">
        <h2 class="display-3">What are you waiting for?</h2>
        <p class="h5">
          Dive into the best moderation experience today! Feel free to join our support server if
          you have any questions or have some feedback to let us know. Have fun and enjoy! :)
        </p>
        <a href="/invite" target="_blank">
          <BaseButton type="primary" size="lg" class="mt-3 mx-2 ml-md-0">
            <span class="h6 font-weight-bold">Add to Discord</span>
          </BaseButton>
        </a>
        <a href="/support" target="_blank">
          <BaseButton type="primary" size="lg" class="mt-3 mx-2 mr-md-0">
            <span class="h6 font-weight-bold">Support Server</span>
          </BaseButton>
        </a>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  layout: 'home',
  async asyncData({ $getContent }) {
    const features = await $getContent('features')
    const images = []
    for (const index of Array(features.length).keys()) {
      images.push(require(`~/assets/images/feature-${index + 1}.png`))
    }

    return { features, images }
  },
}
</script>

<style scoped lang="scss">
.home-feature-column {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.home-feature-image {
  width: 80%;
}

#hero-top-container {
  position: relative;
  top: -76px;
  margin-bottom: -76px;
  width: 100%;
  background: linear-gradient(90deg, #f09819 0%, #ff512f 100%);
  z-index: 0;
}

#hero-top-pattern {
  position: absolute;
  top: 75px;
  width: 100%;
  height: calc(100% - 75px);
  opacity: 0.25;
  z-index: -1;
  overflow: hidden;
}

#hero-top-pattern-inner {
  min-width: 100%;
  min-height: 100%;
}

#hero-top-content {
  position: relative;
  top: 75px;
  height: 75vh;
  min-height: 400px;
}

#hero-top-wave {
  width: 100%;
  height: 10vh;
  margin-bottom: -1px;
}

@include media-breakpoint-up(sm) {
  #hero-top-content {
    height: 65vh;
  }

  #hero-top-wave {
    height: 20vh;
  }
}

.hero-top-column {
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 80%;
}

@include media-breakpoint-up(sm) {
  .hero-top-column {
    height: 100%;
  }
}

#hero-top-icon-sm {
  height: 40vw;
  max-width: 100%;
}

#hero-top-icon {
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 35vw;
  max-height: 55%;
}

#hero-bottom-container {
  width: 100%;
  background: linear-gradient(90deg, #f09819 0%, #ff512f 100%);
  z-index: -1;
}

#hero-bottom-wave {
  width: 100%;
  height: 10vh;
  margin-top: -1px;
}

@include media-breakpoint-up(sm) {
  #hero-bottom-wave {
    height: 20vh;
  }
}
</style>
