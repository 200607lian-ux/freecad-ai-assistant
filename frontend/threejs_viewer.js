        // ===================================
        // Three.js 3D 查看器
        // ===================================
        
        let scene, camera, renderer, controls, currentMesh;
        let isWireframe = false;
        let currentSTLData = null;
        
        function init3DViewer() {
            const canvas = document.getElementById('threeCanvas');
            const container = document.getElementById('modelViewer');
            
            if (!canvas || !container) {
                console.error('找不到 3D 查看器容器');
                return;
            }
            
            // 创建场景
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x1a1a2e);
            
            // 创建相机
            const width = container.clientWidth;
            const height = container.clientHeight;
            camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
            camera.position.set(5, 5, 5);
            camera.lookAt(0, 0, 0);
            
            // 创建渲染器
            renderer = new THREE.WebGLRenderer({ 
                canvas: canvas, 
                antialias: true,
                alpha: true
            });
            renderer.setSize(width, height);
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.shadowMap.enabled = true;
            
            // 添加轨道控制器
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.enableZoom = true;
            controls.zoomSpeed = 1.0;
            controls.minDistance = 0.1;
            controls.maxDistance = 500;
            
            // 添加灯光
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambientLight);
            
            const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight1.position.set(5, 5, 5);
            scene.add(directionalLight1);
            
            const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.4);
            directionalLight2.position.set(-5, 3, -5);
            scene.add(directionalLight2);
            
            // 添加坐标轴
            const axesHelper = new THREE.AxesHelper(3);
            scene.add(axesHelper);
            
            // 窗口大小改变时调整
            window.addEventListener('resize', onWindowResize, false);
            
            // 启动渲染循环
            animate();
            
            console.log('3D 查看器初始化完成');
        }
        
        function animate() {
            requestAnimationFrame(animate);
            
            if (controls) {
                controls.update();
            }
            
            if (renderer && scene && camera) {
                renderer.render(scene, camera);
            }
        }
        
        function onWindowResize() {
            const container = document.getElementById('modelViewer');
            if (!container) return;
            
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            if (camera) {
                camera.aspect = width / height;
                camera.updateProjectionMatrix();
            }
            
            if (renderer) {
                renderer.setSize(width, height);
            }
        }
        
        function loadSTLFromBase64(base64Data) {
            console.log('加载 STL 数据...');
            
            setModelLoading(true);
            
            try {
                // 隐藏占位符
                const placeholder = document.getElementById('viewerPlaceholder');
                if (placeholder) {
                    placeholder.style.display = 'none';
                }
                
                // 显示控制栏
                const viewerControls = document.getElementById('viewerControls');
                if (viewerControls) {
                    viewerControls.style.display = 'flex';
                }
                
                // 解码 Base64
                const binaryString = atob(base64Data);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                
                // 使用 STLLoader 加载
                const loader = new THREE.STLLoader();
                let geometry = loader.parse(bytes.buffer);
                
                // 重要：修复坐标轴对齐问题
                // FreeCAD 使用 Z 轴向上，Three.js 使用 Y 轴向上
                geometry.rotateX(-Math.PI / 2);
                
                // 重新计算几何体
                geometry.computeBoundingBox();
                
                // 移除旧模型
                if (currentMesh) {
                    scene.remove(currentMesh);
                    currentMesh.geometry.dispose();
                    currentMesh.material.dispose();
                }
                
                // 创建材质（橙色金属效果）
                const material = new THREE.MeshPhongMaterial({
                    color: 0xff8c42,
                    specular: 0x444444,
                    shininess: 100,
                    flatShading: false,
                    side: THREE.DoubleSide,
                    wireframe: isWireframe
                });
                
                // 创建网格
                currentMesh = new THREE.Mesh(geometry, material);
                
                // 居中模型
                const center = new THREE.Vector3();
                geometry.boundingBox.getCenter(center);
                currentMesh.position.sub(center);
                
                // 添加到场景
                scene.add(currentMesh);
                
                // 自动调整相机位置
                const modelSize = new THREE.Vector3();
                geometry.boundingBox.getSize(modelSize);
                const maxDim = Math.max(modelSize.x, modelSize.y, modelSize.z);
                const fov = camera.fov * (Math.PI / 180);
                let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));
                cameraZ *= 2.5;
                
                camera.position.set(cameraZ, cameraZ * 0.8, cameraZ);
                camera.lookAt(0, 0, 0);
                
                if (controls && typeof controls.update === 'function') {
                    controls.update();
                }
                
                // 保存 STL 数据
                currentSTLData = base64Data;
                
                setModelLoading(false);
                
                console.log('STL 模型加载成功');
                console.log('  顶点数:', geometry.attributes.position.count);
                console.log('  尺寸:', modelSize.x.toFixed(2), 'x', modelSize.y.toFixed(2), 'x', modelSize.z.toFixed(2));
                
            } catch (error) {
                console.error('STL 加载失败:', error);
                setModelLoading(false);
                addMessage('error', '3D 模型加载失败: ' + error.message);
            }
        }
        
        function toggleWireframe() {
            if (currentMesh) {
                isWireframe = !isWireframe;
                currentMesh.material.wireframe = isWireframe;
            }
        }
        
        function resetView() {
            if (currentMesh) {
                const geometry = currentMesh.geometry;
                geometry.computeBoundingBox();
                const modelSize = new THREE.Vector3();
                geometry.boundingBox.getSize(modelSize);
                const maxDim = Math.max(modelSize.x, modelSize.y, modelSize.z);
                const fov = camera.fov * (Math.PI / 180);
                let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));
                cameraZ *= 2.5;
                
                camera.position.set(cameraZ, cameraZ * 0.8, cameraZ);
                camera.lookAt(0, 0, 0);
                controls.reset();
            }
        }
        
