# Esquema de Colores - Alaba+

## Colores Principales

### Color Primario (Azul)
- **primary**: `#0B7FB3` - Color principal del sistema
- **primary-dark**: `#095E87` - Versión oscura para hover/estados activos
- **primary-light**: `#0D9FE0` - Versión clara para fondos sutiles

### Colores Neutros
- **black**: `#121212` - Negro principal
- **dark-gray**: `#292929` - Gris oscuro
- **gray**: `#4a4a4a` - Gris medio
- **light-gray**: `#e5e5e5` - Gris claro para bordes
- **white**: `#ffffff` - Blanco

## Uso en Templates

### Botones Principales
```html
<!-- Botón primario -->
<button class="bg-primary hover:bg-primary-dark text-white">
    Guardar
</button>

<!-- Botón secundario -->
<button class="border border-primary text-primary hover:bg-primary hover:text-white">
    Cancelar
</button>
```

### Navegación Activa
```html
<!-- Item activo -->
<a class="bg-primary text-white">Dashboard</a>

<!-- Item normal -->
<a class="text-gray hover:text-primary">Miembros</a>
```

### Iconos y Badges
```html
<!-- Icono con color primario -->
<i class="fa-solid fa-users text-primary"></i>

<!-- Badge -->
<span class="bg-primary-light text-primary px-2 py-1 rounded">Activo</span>
```

### Fondos y Tarjetas
```html
<!-- Card con borde primario -->
<div class="border-l-4 border-primary bg-white p-4">
    Contenido destacado
</div>

<!-- Fondo sutil -->
<div class="bg-primary-light/10 p-4">
    Información importante
</div>
```

## Ejemplos de Reemplazo

Para actualizar los componentes existentes de negro a azul:

### Antes (Negro)
```html
<button class="bg-black hover:bg-dark-gray text-white">
```

### Después (Azul)
```html
<button class="bg-primary hover:bg-primary-dark text-white">
```

### Antes (Negro)
```html
<div class="w-12 h-12 bg-black rounded">
```

### Después (Azul)
```html
<div class="w-12 h-12 bg-primary rounded">
```

## Paleta de Colores Completa

```
Primary:       #0B7FB3 ████████
Primary Dark:  #095E87 ████████
Primary Light: #0D9FE0 ████████

Black:         #121212 ████████
Dark Gray:     #292929 ████████
Gray:          #4a4a4a ████████
Light Gray:    #e5e5e5 ████████
White:         #ffffff ████████
```

## Accesibilidad

- **Contraste Primary/White**: 4.5:1 ✓ (WCAG AA)
- **Contraste Primary-Dark/White**: 7:1 ✓ (WCAG AAA)
- **Contraste Gray/White**: 9:1 ✓ (WCAG AAA)

## Recomendaciones

1. **Botones de acción**: Usar `bg-primary` con `hover:bg-primary-dark`
2. **Links**: Usar `text-primary` con `hover:text-primary-dark`
3. **Elementos activos**: Usar `bg-primary` con `text-white`
4. **Iconos destacados**: Usar `text-primary`
5. **Fondos sutiles**: Usar `bg-primary-light/10` o `bg-primary-light/20`
