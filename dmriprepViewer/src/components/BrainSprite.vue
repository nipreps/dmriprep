<template>
  <div class="brainsprite">
        <div v-if="!done">Hold on...</div>
        <canvas :id="id"></canvas>
        <img :id="id+'_spriteImg'"
         class="hidden"
         :src="'data:image/png;base64,' + base"
         v-if="showOrig"
        />
        <img :id="id+'_overlayImg'"
         class="hidden"
         v-if="overlay && showOrig"
         :src="'data:image/png;base64,' + overlay"
        />
  </div>
</template>

<style scoped>
  .hidden {
    visibility: hidden;
    /* display: none; */
  }
  canvas {
    width: 100%;
  }
  img {
    /* width: 10px;
    height: 10px; */
  }
</style>

<script>
import brainsprite from './brainsprite';

export default {
  name: 'brainsprite',
  props: ['base', 'overlay', 'id',
    'base_dim_x', 'base_dim_y',
    'overlay_dim_x', 'overlay_dim_y'],
  data() {
    return {
      brain: null,
      showOrig: true,
      done: false,
      ready: false,
    };
  },
  methods: {
    initBrainSprite() {
      /* eslint-disable-next-line */
      const brain = new brainsprite({
        canvas: this.id,
        sprite: `${this.id}_spriteImg`,
        nbSlice: { Y: this.base_dim_x, Z: this.base_dim_y },
        overlay: {
          sprite: `${this.id}_overlayImg`,
          nbSlice: { Y: this.overlay_dim_x, Z: this.overlay_dim_y },
          opacity: 0.5,
        },
      });
      this.brain = brain;
      this.showOrig = false;
      this.done = true;
    },
  },
  mounted() {
    this.$nextTick(() => {
      setTimeout(() => {
        this.ready = true;
        this.initBrainSprite();
      }, 100);
    });
  },
};
</script>
