import { computed, reactive, ref } from 'vue'

function createSeededRandom(seed) {
  let value = seed % 2147483647
  if (value <= 0) value += 2147483646
  return () => {
    value = value * 16807 % 2147483647
    return (value - 1) / 2147483646
  }
}

function createParticles(count) {
  const random = createSeededRandom(count * 97 + 13)
  return Array.from({ length: count }, (_, index) => {
    const size = Math.round((random() * 4 + 1.5) * 10) / 10
    const duration = Math.round(random() * 20 + 16)
    const delay = Math.round(random() * -20)
    return {
      id: `particle-${count}-${index}`,
      style: {
        width: `${size}px`,
        height: `${size}px`,
        left: `${Math.round(random() * 1000) / 10}%`,
        top: `${Math.round(random() * 1000) / 10}%`,
        animationDuration: `${duration}s`,
        animationDelay: `${delay}s`,
        opacity: (random() * 0.35 + 0.12).toFixed(2),
        boxShadow: `0 0 ${Math.round(size * 5)}px rgba(34, 246, 255, 0.4)`
      }
    }
  })
}

export function useAmbientEffects(options = {}) {
  const {
    particleCount = 24,
    parallaxFactor = 0.006
  } = options

  const containerRef = ref(null)
  const pointer = reactive({
    x: 0,
    y: 0,
    active: false
  })

  const particles = createParticles(particleCount)

  const parallaxStyle = computed(() => ({
    transform: pointer.active
      ? `translate3d(${(pointer.x - 240) * parallaxFactor}px, ${(pointer.y - 180) * parallaxFactor}px, 0)`
      : 'translate3d(0, 0, 0)'
  }))

  const mouseGlowStyle = computed(() => ({
    left: `${pointer.x - 140}px`,
    top: `${pointer.y - 140}px`,
    opacity: pointer.active ? 1 : 0
  }))

  function handleMouseMove(event) {
    if (!containerRef.value) return
    const rect = containerRef.value.getBoundingClientRect()
    pointer.x = event.clientX - rect.left
    pointer.y = event.clientY - rect.top
    pointer.active = true
  }

  function handleMouseLeave() {
    pointer.active = false
  }

  function handleTiltMove(event) {
    const element = event.currentTarget
    const rect = element.getBoundingClientRect()
    const offsetX = event.clientX - rect.left
    const offsetY = event.clientY - rect.top
    const rotateX = ((offsetY / rect.height) - 0.5) * -16
    const rotateY = ((offsetX / rect.width) - 0.5) * 18

    element.style.setProperty('--pointer-x', `${offsetX}px`)
    element.style.setProperty('--pointer-y', `${offsetY}px`)
    element.style.setProperty('--pointer-opacity', '1')
    element.style.transform = `perspective(1200px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translate3d(0, -8px, 18px)`
  }

  function handleTiltLeave(event) {
    const element = event.currentTarget
    element.style.setProperty('--pointer-opacity', '0')
    element.style.transform = ''
  }

  function triggerRipple(event) {
    const element = event.currentTarget
    const rect = element.getBoundingClientRect()
    const ripple = document.createElement('span')
    ripple.className = 'infuse-ripple-node'
    ripple.style.left = `${event.clientX - rect.left}px`
    ripple.style.top = `${event.clientY - rect.top}px`
    element.appendChild(ripple)
    window.setTimeout(() => ripple.remove(), 700)
  }

  return {
    containerRef,
    particles,
    parallaxStyle,
    mouseGlowStyle,
    handleMouseMove,
    handleMouseLeave,
    handleTiltMove,
    handleTiltLeave,
    triggerRipple
  }
}
