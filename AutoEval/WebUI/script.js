
    // DOM 元素
    const refreshBtn = document.getElementById('refreshBtn');
    const addBtn = document.getElementById('addBtn');
    const updateBtn = document.getElementById('updateBtn');
    const statusBar = document.getElementById('statusBar');
    const modelList = document.getElementById('modelList');

    // 当前数据状态
    let jsonData = {};

    // 事件监听器
    refreshBtn.addEventListener('click', fetchData);
    addBtn.addEventListener('click', addNewModel);
    updateBtn.addEventListener('click', updateData);

    // 初始化
    document.addEventListener('DOMContentLoaded', () => {
        fetchData();
        fetchEvaluationData(); // 添加评测数据加载
    });

    // 从后端获取数据（智能降级）
    function fetchData() {
        statusBar.textContent = "正在连接后端服务...";
        modelList.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                正在加载数据...
            </div>
        `;

        // 首先尝试连接后端服务
        fetch('http://localhost:8009/config', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            // 设置较短的超时时间
            signal: AbortSignal.timeout(3000)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('后端服务响应错误: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            // 后端服务可用
            jsonData = data;
            isUsingMockData = false;
            backendAvailable = true;
            renderModelList();
            statusBar.textContent = "✅ 已连接到后端服务 | 模型数量: " + Object.keys(jsonData).length;
            console.log('成功连接到后端服务');
        })
        .catch(async error => {
            console.log('后端连接失败，切换到模拟数据模式:', error.message);
            
            // 使用模拟数据
            if (window.mockDataManager) {
                // 确保数据管理器已初始化
                if (!window.mockDataManager.dataLoader.isDataLoaded()) {
                    await window.mockDataManager.initialize();
                }
                jsonData = window.mockDataManager.getData();
                isUsingMockData = true;
                backendAvailable = false;
                renderModelList();
                statusBar.textContent = "⚠️ 后端服务不可用，已切换到模拟数据模式 | 模型数量: " + Object.keys(jsonData).length;
                console.log('已切换到模拟数据模式');
            } else {
                // 如果mock.js未加载，显示错误
                statusBar.textContent = "❌ 后端服务不可用，且模拟数据未加载";
                modelList.innerHTML = `
                    <div class="loading" style="color: #e53e3e;">
                        <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 15px;"></i>
                        <p>无法连接到后端服务: ${error.message}</p>
                        <p>请检查后端服务是否运行在端口8009，或确保mock.js文件已正确加载</p>
                    </div>
                `;
            }
        });
    }

    // 渲染模型列表
    function renderModelList() {
        let tableHTML = `
            <table class="model-table">
                <thead>
                    <tr>
                        <th style="width: 50px;">ID</th>
                        <th style="width: 100px;">训完</th>
                        <th class="model-info-column">模型信息</th>
                        <th style="width: 120px;">VLMEvalKit</th>
                        <th style="width: 200px;">VLMEvalKit 数据集</th>
                        <th class="vlm-cot-column">VLM_COT</th>
                        <th class="vlm-cot-dataset-column">VLM_COT 数据集</th>
                        <th style="width: 40px;">MIRB</th>
                        <th style="width: 40px;">mmiu</th>
                    </tr>
                </thead>
                <tbody>
        `;

        // 按ID排序
        const sortedIds = Object.keys(jsonData).sort();

        sortedIds.forEach(id => {
            const model = jsonData[id];
            const vlmevalkitDatasets = model.Eval_Statu.VLMEvalKit.Datasets.split(',').map(d => d.trim()).filter(d => d);
            const vlmevalkitCotDatasets = model.Eval_Statu.VLMEvalKit_COT.Datasets.split(',').map(d => d.trim()).filter(d => d);
            const isVLMEvalKitCompleted = model.Eval_Statu.VLMEvalKit.Statu == 1;
            const isVLMEvalKitCOTCompleted = model.Eval_Statu.VLMEvalKit_COT.Statu == 1;

            tableHTML += `
                <tr>
                    <td class="id-cell">
                        <div class="model-id">${id}</div>
                        <button class="delete-btn" data-id="${id}">Del</button>
                    </td>
                    <td class="training-time-column">
                        <div class="compact-input-group">
                            <input type="date" class="input-field compact-input-field trained-date" value="${model.data.trained_date}" data-id="${id}">
                            <input type="time" class="input-field compact-input-field trained-time" value="${model.data.trained_time}" data-id="${id}">
                        </div>
                    </td>
                    <td class="model-info-column">
                        <div class="compact-input-group">
                            <input type="text" class="input-field compact-input-field model-path" value="${model.data.model_path}" data-id="${id}" placeholder="模型路径">
                            <input type="text" class="input-field compact-input-field model-name" value="${model.data.model_name}" data-id="${id}" placeholder="模型名称">
                        </div>
                    </td>
                    <td>
                        <div class="input-group">
                            <select class="input-field vlmevalkit-status ${!isVLMEvalKitCompleted ? 'status-not-completed' : ''}" data-id="${id}">
                                <option value="0" ${!isVLMEvalKitCompleted ? 'selected' : ''}>待评</option>
                                <option value="1" ${isVLMEvalKitCompleted ? 'selected' : ''}>已评</option>
                            </select>
                        </div>
                    </td>
                    <td>
                        <div class="dataset-selector" data-id="${id}" data-type="vlmevalkit">
                            <div class="dataset-display">
                                <div class="dataset-display-input">
                                    ${vlmevalkitDatasets.length > 0 ?
                                        `<div class="dataset-tags">
                                            ${vlmevalkitDatasets.slice(0, 3).map(d => `<span class="dataset-tag">${d}</span>`).join('')}
                                            ${vlmevalkitDatasets.length > 3 ? `<span class="dataset-tag">+${vlmevalkitDatasets.length - 3}更多</span>` : ''}
                                        </div>` :
                                        '无'}
                                </div>
                                <button class="dataset-toggle-btn">+</button>
                            </div>
                            <div class="dataset-dropdown">
                                <div class="dataset-actions">
                                    <button class="btn btn-sm btn-primary select-all-btn">全选</button>
                                    <button class="btn btn-sm btn-primary invert-selection-btn">反选</button>
                                </div>
                                                            ${(window.predefinedDatasets || predefinedDatasets).map(dataset => `
                                <div class="dataset-item">
                                    <input type="checkbox" class="dataset-checkbox"
                                        ${vlmevalkitDatasets.includes(dataset) ? 'checked' : ''}
                                        value="${dataset}">
                                    <span>${dataset}</span>
                                </div>
                            `).join('')}
                            </div>
                        </div>
                    </td>
                    <td class="vlm-cot-column">
                        <div class="input-group">
                            <select class="input-field vlmevalkit-cot-status ${!isVLMEvalKitCOTCompleted ? 'status-not-completed' : ''}" data-id="${id}">
                                <option value="0" ${!isVLMEvalKitCOTCompleted ? 'selected' : ''}>待评</option>
                                <option value="1" ${isVLMEvalKitCOTCompleted ? 'selected' : ''}>已评</option>
                            </select>
                        </div>
                    </td>
                    <td class="vlm-cot-dataset-column">
                        <div class="dataset-selector" data-id="${id}" data-type="vlmevalkit-cot">
                            <div class="dataset-display">
                                <div class="dataset-display-input">
                                    ${vlmevalkitCotDatasets.length > 0 ?
                                        `<div class="dataset-tags">
                                            ${vlmevalkitCotDatasets.slice(0, 3).map(d => `<span class="dataset-tag">${d}</span>`).join('')}
                                            ${vlmevalkitCotDatasets.length > 3 ? `<span class="dataset-tag">+${vlmevalkitCotDatasets.length - 3}更多</span>` : ''}
                                        </div>` :
                                        '无'}
                                </div>
                                <button class="dataset-toggle-btn">+</button>
                            </div>
                            <div class="dataset-dropdown">
                                <div class="dataset-actions">
                                    <button class="btn btn-sm btn-primary select-all-btn">全选</button>
                                    <button class="btn btn-sm btn-primary invert-selection-btn">反选</button>
                                </div>
                                                            ${(window.predefinedDatasets || predefinedDatasets).map(dataset => `
                                <div class="dataset-item">
                                    <input type="checkbox" class="dataset-checkbox"
                                        ${vlmevalkitCotDatasets.includes(dataset) ? 'checked' : ''}
                                        value="${dataset}">
                                    <span>${dataset}</span>
                                </div>
                            `).join('')}
                            </div>
                        </div>
                    </td>
                    <td>
                        <div class="checkbox-group">
                            <input type="checkbox" class="checkbox mirb-status"
                                ${model.Eval_Statu.MIRB == 1 ? 'checked' : ''}
                                data-id="${id}">
                        </div>
                    </td>
                    <td>
                        <div class="checkbox-group">
                            <input type="checkbox" class="checkbox mmiu-status"
                                ${model.Eval_Statu.mmiu == 1 ? 'checked' : ''}
                                data-id="${id}">
                        </div>
                    </td>
                </tr>
            `;
        });

        tableHTML += `
                </tbody>
            </table>
        `;

        modelList.innerHTML = tableHTML;

        // 添加数据集选择器事件
        setupDatasetSelectors();

        // 添加状态变化监听
        document.querySelectorAll('.vlmevalkit-status, .vlmevalkit-cot-status').forEach(select => {
            select.addEventListener('change', function() {
                if (this.value === '0') {
                    this.classList.add('status-not-completed');
                } else {
                    this.classList.remove('status-not-completed');
                }
            });
        });

        // 添加删除按钮事件
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const id = this.getAttribute('data-id');
                if (confirm(`确定要删除ID为 ${id} 的模型配置吗？`)) {
                    // 如果是模拟数据模式，使用模拟API
                    if (isUsingMockData && window.mockDataManager) {
                        window.mockDataManager.deleteModel(id)
                            .then(result => {
                                delete jsonData[id];
                                renderModelList();
                                statusBar.textContent = "✅ " + result.message;
                                console.log('模拟数据删除成功:', result);
                            })
                            .catch(error => {
                                statusBar.textContent = "❌ 模拟数据删除失败: " + error.message;
                                console.error('模拟数据删除失败:', error);
                            });
                    } else {
                        delete jsonData[id];
                        updateData();
                    }
                }
            });
        });
    }

    // 新增模型配置（智能降级）
    function addNewModel() {
        // 生成新ID (当前最大ID + 1)
        const ids = Object.keys(jsonData).map(id => parseInt(id));
        const newId = ids.length > 0 ? (Math.max(...ids) + 1).toString() : '1';

        // 获取当前日期和时间
        const today = new Date();
        const formattedDate = today.toISOString().split('T')[0];

        // 创建新模型配置
        const newModel = {
            data: {
                trained_date: formattedDate,
                trained_time: "23:00",
                model_path: "",
                model_name: ""
            },
            Eval_Statu: {
                VLMEvalKit: {
                    Statu: 0,
                    Datasets: "MMMU_DEV_VAL"
                },
                VLMEvalKit_COT: {
                    Statu: 0,
                    Datasets: "MMMU_DEV_VAL"
                },
                MIRB: 1,
                mmiu: 1
            }
        };

        // 添加到数据
        jsonData[newId] = newModel;

        // 如果是模拟数据模式，使用模拟API
        if (isUsingMockData) {
            if (window.mockDataManager) {
                window.mockDataManager.addModel(newModel)
                    .then(result => {
                        statusBar.textContent = "✅ " + result.message;
                        console.log('模拟数据新增成功:', result);
                    })
                    .catch(error => {
                        statusBar.textContent = "❌ 模拟数据新增失败: " + error.message;
                        console.error('模拟数据新增失败:', error);
                    });
            } else {
                statusBar.textContent = "✅ 已添加新模型配置 (ID: " + newId + ") - 模拟模式";
            }
        } else {
            statusBar.textContent = "✅ 已添加新模型配置 (ID: " + newId + ") - 后端模式";
        }

        // 重新渲染列表
        renderModelList();

        // 滚动到顶部
        document.querySelector('.model-table-container').scrollTo(0, 0);
    }

    // 设置数据集选择器功能
    function setupDatasetSelectors() {
        // 切换下拉框显示
        document.querySelectorAll('.dataset-toggle-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const selector = this.closest('.dataset-selector');
                const dropdown = selector.querySelector('.dataset-dropdown');

                // 关闭所有其他下拉框
                document.querySelectorAll('.dataset-dropdown').forEach(d => {
                    if (d !== dropdown) {
                        d.classList.remove('show');
                        d.previousElementSibling.querySelector('.dataset-toggle-btn').textContent = '+';
                    }
                });

                // 切换显示状态
                dropdown.classList.toggle('show');

                // 切换按钮文本
                if (dropdown.classList.contains('show')) {
                    this.textContent = '✓';

                    // 确保下拉框可见
                    setTimeout(() => {
                        dropdown.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }, 10);
                } else {
                    this.textContent = '+';

                    // 更新显示框的值
                    const type = selector.getAttribute('data-type');
                    const displayInput = selector.querySelector('.dataset-display-input');
                    const id = selector.getAttribute('data-id');

                    // 获取选中的数据集
                    const selected = Array.from(selector.querySelectorAll('.dataset-checkbox:checked'))
                        .map(cb => cb.value);

                    // 更新显示
                    if (selected.length > 0) {
                        displayInput.innerHTML = `
                            <div class="dataset-tags">
                                ${selected.slice(0, 3).map(d => `<span class="dataset-tag">${d}</span>`).join('')}
                                ${selected.length > 3 ? `<span class="dataset-tag">+${selected.length - 3}更多</span>` : ''}
                            </div>
                        `;
                    } else {
                        displayInput.textContent = '无';
                    }
                }
            });
        });

        // 全选按钮事件
        document.querySelectorAll('.select-all-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const dropdown = this.closest('.dataset-dropdown');
                dropdown.querySelectorAll('.dataset-checkbox').forEach(checkbox => {
                    checkbox.checked = true;
                });
            });
        });

        // 反选按钮事件
        document.querySelectorAll('.invert-selection-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const dropdown = this.closest('.dataset-dropdown');
                dropdown.querySelectorAll('.dataset-checkbox').forEach(checkbox => {
                    checkbox.checked = !checkbox.checked;
                });
            });
        });

        // 点击其他地方关闭下拉框
        document.addEventListener('click', function() {
            document.querySelectorAll('.dataset-dropdown').forEach(dropdown => {
                dropdown.classList.remove('show');
            });

            document.querySelectorAll('.dataset-toggle-btn').forEach(btn => {
                btn.textContent = '+';
            });
        });

        // 阻止下拉框内部点击事件冒泡
        document.querySelectorAll('.dataset-dropdown').forEach(dropdown => {
            dropdown.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        });

        // 允许调整下拉框大小
        document.querySelectorAll('.dataset-dropdown').forEach(dropdown => {
            dropdown.addEventListener('mousedown', function(e) {
                if (e.target === dropdown) {
                    e.preventDefault();
                    let startX = e.clientX;
                    let startY = e.clientY;
                    let startWidth = dropdown.offsetWidth;
                    let startHeight = dropdown.offsetHeight;

                    function doDrag(e) {
                        dropdown.style.width = (startWidth + e.clientX - startX) + 'px';
                        dropdown.style.height = (startHeight + e.clientY - startY) + 'px';
                    }

                    function stopDrag() {
                        document.documentElement.removeEventListener('mousemove', doDrag, false);
                        document.documentElement.removeEventListener('mouseup', stopDrag, false);
                    }

                    document.documentElement.addEventListener('mousemove', doDrag, false);
                    document.documentElement.addEventListener('mouseup', stopDrag, false);
                }
            });
        });
    }

    // 更新数据到后端
    function updateData() {
        // 收集所有更改
        const allIds = Object.keys(jsonData);

        allIds.forEach(id => {
            const modelCard = document.querySelector(`[data-id="${id}"]`).closest('tr');

            if (modelCard) {
                // 更新数据部分
                jsonData[id].data = {
                    trained_date: modelCard.querySelector('.trained-date').value,
                    trained_time: modelCard.querySelector('.trained-time').value,
                    model_path: modelCard.querySelector('.model-path').value,
                    model_name: modelCard.querySelector('.model-name').value
                };

                // 获取VLMEvalKit数据集
                const vlmevalkitSelector = modelCard.querySelector('.dataset-selector[data-type="vlmevalkit"]');
                const vlmevalkitDatasets = Array.from(vlmevalkitSelector.querySelectorAll('.dataset-checkbox:checked'))
                    .map(cb => cb.value);

                // 获取VLMEvalKit_COT数据集
                const vlmevalkitCotSelector = modelCard.querySelector('.dataset-selector[data-type="vlmevalkit-cot"]');
                const vlmevalkitCotDatasets = Array.from(vlmevalkitCotSelector.querySelectorAll('.dataset-checkbox:checked'))
                    .map(cb => cb.value);

                // 更新评估状态部分
                jsonData[id].Eval_Statu = {
                    VLMEvalKit: {
                        Statu: parseInt(modelCard.querySelector('.vlmevalkit-status').value),
                        Datasets: vlmevalkitDatasets.join(', ')
                    },
                    VLMEvalKit_COT: {
                        Statu: parseInt(modelCard.querySelector('.vlmevalkit-cot-status').value),
                        Datasets: vlmevalkitCotDatasets.join(', ')
                    },
                    MIRB: modelCard.querySelector('.mirb-status').checked ? 1 : 0,
                    mmiu: modelCard.querySelector('.mmiu-status').checked ? 1 : 0
                };
            }
        });

        // 如果是模拟数据模式，使用模拟API
        if (isUsingMockData) {
            statusBar.textContent = "正在更新模拟数据...";
            
            if (window.mockDataManager) {
                window.mockDataManager.updateData(jsonData)
                    .then(result => {
                        statusBar.textContent = "✅ 模拟数据更新成功 | " + result.message;
                        console.log('模拟数据已更新:', result);
                    })
                    .catch(error => {
                        statusBar.textContent = "❌ 模拟数据更新失败: " + error.message;
                        console.error('模拟数据更新失败:', error);
                    });
            } else {
                statusBar.textContent = "❌ 模拟数据管理器未加载";
            }
            return;
        }

        // 发送更新到后端
        statusBar.textContent = "正在更新后端数据...";

        fetch('http://localhost:8009/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jsonData),
            signal: AbortSignal.timeout(5000)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('后端更新失败: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            statusBar.textContent = "✅ 后端数据更新成功 | " + (data.message || "");
            console.log('后端数据更新成功:', data);
            setTimeout(fetchData, 1000); // 1秒后刷新数据
        })
        .catch(error => {
            console.error('后端更新失败:', error);
            statusBar.textContent = "❌ 后端更新失败，已切换到模拟数据模式";
            isUsingMockData = true;
            backendAvailable = false;
            
            // 自动切换到模拟数据
            if (window.mockDataManager) {
                jsonData = window.mockDataManager.getData();
                renderModelList();
            }
        });
    }

    // 获取评测状态数据
    function fetchEvaluationData() {
        const evalLoading = document.getElementById('evalLoading');
        const evalContent = document.getElementById('evalContent');
        
        if (!evalLoading || !evalContent) return;
        
        evalLoading.style.display = 'block';
        evalContent.style.display = 'none';

        // 首先尝试从后端获取评测数据
        fetch('http://localhost:5001/evaluated', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            signal: AbortSignal.timeout(3000)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('后端服务响应错误: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            evalLoading.style.display = 'none';
            evalContent.style.display = 'block';
            renderEvaluationTable(data);
        })
        .catch(async error => {
            console.log('后端评测数据连接失败，使用模拟数据:', error.message);
            
            // 使用模拟数据
            if (window.mockAPI) {
                try {
                    const mockData = await window.mockAPI.getEvaluated();
                    evalLoading.style.display = 'none';
                    evalContent.style.display = 'block';
                    renderEvaluationTable(mockData);
                } catch (mockError) {
                    showEvaluationError('模拟数据加载失败: ' + mockError.message);
                }
            } else {
                showEvaluationError('无法加载评测数据，请确保mock.js已正确加载');
            }
        });
    }

    // 显示评测数据错误
    function showEvaluationError(message) {
        const evalLoading = document.getElementById('evalLoading');
        const evalContent = document.getElementById('evalContent');
        
        if (evalLoading) evalLoading.style.display = 'none';
        if (evalContent) {
            evalContent.style.display = 'block';
            evalContent.innerHTML = `
                <div class="loading" style="color: #e53e3e;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 15px;"></i>
                    <p>${message}</p>
                </div>
            `;
        }
    }

    // 渲染评测状态表格
    function renderEvaluationTable(data) {
        const table = document.getElementById('evalTable');
        const tableBody = document.getElementById('evalTableBody');
        
        if (!table || !tableBody) return;
        
        const evaluationStatus = data.evaluation_status;
        const commonStandard = data.common_datasets.standard || [];
        const commonCOT = data.common_datasets.COT || [];

        // 获取所有模型名称并排序
        const modelNames = Object.keys(evaluationStatus).sort();

        // 检查是否有数据
        if (modelNames.length === 0 || (commonStandard.length === 0 && commonCOT.length === 0)) {
            showEvaluationError('没有可用的评测数据');
            return;
        }

        // 清空现有内容
        tableBody.innerHTML = '';
        const headerRow = table.querySelector('thead tr');
        // 保留第一列（模型名称），删除其他列
        while (headerRow.children.length > 1) {
            headerRow.removeChild(headerRow.lastChild);
        }

        // 添加Standard部分标题和数据列
        if (commonStandard.length > 0) {
            const standardHeader = document.createElement('th');
            standardHeader.textContent = 'Standard';
            standardHeader.className = 'standard-header section-header';
            standardHeader.colSpan = commonStandard.length;
            headerRow.appendChild(standardHeader);

            // 添加Standard数据集列
            commonStandard.forEach(dataset => {
                const datasetHeader = document.createElement('th');
                datasetHeader.textContent = dataset;
                datasetHeader.className = 'dataset-col dataset-name';
                headerRow.appendChild(datasetHeader);
            });
        }

        // 添加COT部分标题和数据列
        if (commonCOT.length > 0) {
            const cotHeader = document.createElement('th');
            cotHeader.textContent = 'COT';
            cotHeader.className = 'cot-header section-header';
            cotHeader.colSpan = commonCOT.length;
            headerRow.appendChild(cotHeader);

            // 添加COT数据集列
            commonCOT.forEach(dataset => {
                const datasetHeader = document.createElement('th');
                datasetHeader.textContent = dataset;
                datasetHeader.className = 'dataset-col dataset-name';
                headerRow.appendChild(datasetHeader);
            });
        }

        // 为每个模型创建行
        modelNames.forEach(model => {
            const modelRow = document.createElement('tr');

            // 模型名称单元格
            const modelNameCell = document.createElement('td');
            modelNameCell.textContent = model;
            modelNameCell.className = 'model-name';
            modelRow.appendChild(modelNameCell);

            // Standard评测状态
            commonStandard.forEach(dataset => {
                const score = evaluationStatus[model].standard[dataset] || 0;
                const statusCell = document.createElement('td');
                
                if (score > 0) {
                    // 有分数，显示分数
                    statusCell.textContent = score.toFixed(1);
                    statusCell.className = 'evaluated-score';
                    
                    // 根据分数设置颜色
                    if (score >= 90) {
                        statusCell.classList.add('high');
                    } else if (score >= 80) {
                        statusCell.classList.add('medium');
                    } else {
                        statusCell.classList.add('low');
                    }
                } else {
                    // 无分数，显示未评测
                    statusCell.textContent = '✗';
                    statusCell.className = 'not-evaluated';
                }
                
                statusCell.title = `${dataset} (Standard)`;
                modelRow.appendChild(statusCell);
            });

            // COT评测状态
            commonCOT.forEach(dataset => {
                const score = evaluationStatus[model].COT[dataset] || 0;
                const statusCell = document.createElement('td');
                
                if (score > 0) {
                    // 有分数，显示分数
                    statusCell.textContent = score.toFixed(1);
                    statusCell.className = 'evaluated-score';
                    
                    // 根据分数设置颜色
                    if (score >= 90) {
                        statusCell.classList.add('high');
                    } else if (score >= 80) {
                        statusCell.classList.add('medium');
                    } else {
                        statusCell.classList.add('low');
                    }
                } else {
                    // 无分数，显示未评测
                    statusCell.textContent = '✗';
                    statusCell.className = 'not-evaluated';
                }
                
                statusCell.title = `${dataset} (COT)`;
                modelRow.appendChild(statusCell);
            });

            tableBody.appendChild(modelRow);
        });

        // 调整表格布局
        adjustEvaluationTableLayout();
    }

    // 调整评测表格布局
    function adjustEvaluationTableLayout() {
        const table = document.getElementById('evalTable');
        if (!table) return;
        
        const containerWidth = table.parentElement.clientWidth;
        const modelNameWidth = 150; // 模型名称列固定宽度
        const availableWidth = containerWidth - modelNameWidth;

        // 获取所有数据集列
        const datasetHeaders = table.querySelectorAll('thead th.dataset-name');
        const totalDatasets = datasetHeaders.length;

        if (totalDatasets > 0) {
            // 计算每列宽度
            const colWidth = Math.max(60, availableWidth / totalDatasets);

            // 应用宽度到数据集列
            datasetHeaders.forEach(header => {
                header.style.width = `${colWidth}px`;
                header.style.minWidth = `${colWidth}px`;
                header.style.maxWidth = `${colWidth}px`;
            });

            // 应用相同宽度到数据单元格
            const dataCells = table.querySelectorAll('tbody td:not(.model-name)');
            dataCells.forEach(cell => {
                cell.style.width = `${colWidth}px`;
                cell.style.minWidth = `${colWidth}px`;
                cell.style.maxWidth = `${colWidth}px`;
            });
        }
    }