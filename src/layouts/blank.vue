<template>
  <div class="blank-layout">
    <slot />
  </div>
</template>

<style scoped>
.blank-layout {
  width: 100%;
  min-height: 100vh;
  margin: 0;
  padding: 0;
  background: #fff;
}
</style>

<style>
/* 全局样式重置，确保没有后台样式干扰 */
.blank-layout * {
  box-sizing: border-box;
}

.blank-layout body {
  margin: 0;
  padding: 0;
}
</style>

