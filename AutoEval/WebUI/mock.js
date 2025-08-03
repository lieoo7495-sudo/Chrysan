// 模拟数据管理器 - 从JSON文件加载数据
class MockDataLoader {
    constructor() {
        this.mockData = null;
        this.predefinedDatasets = [];
        this.evaluationMetrics = {};
        this.modelTypes = {};
        this.systemConfig = {};
        this.metadata = {};
        this.evaluationStatus = {};
        this.commonDatasets = {};
        this.isLoaded = false;
    }

    // 从JSON文件加载数据
    async loadMockData() {
        try {
            const response = await fetch('./mock.json');
            if (!response.ok) {
                throw new Error(`Failed to load mock.json: ${response.status}`);
            }
            const data = await response.json();
            
            this.mockData = data.modelConfigs;
            this.predefinedDatasets = data.datasets.predefined;
            this.evaluationMetrics = data.evaluationMetrics;
            this.modelTypes = data.modelTypes;
            this.systemConfig = data.systemConfig;
            this.metadata = data.metadata;
            this.evaluationStatus = data.evaluationStatus || {};
            this.commonDatasets = data.commonDatasets || {};
            this.isLoaded = true;
            
            console.log('Mock data loaded successfully:', this.metadata);
            return true;
        } catch (error) {
            console.error('Failed to load mock data:', error);
            // 如果加载失败，使用默认数据
            this.useDefaultData();
            return false;
        }
    }

    // 使用默认数据（当JSON文件加载失败时）
    useDefaultData() {
        this.mockData = {
            "1": {
                "data": {
                    "trained_date": "2024-01-15",
                    "trained_time": "14:30",
                    "model_path": "/models/llama2-7b-chat",
                    "model_name": "LLaMA2-7B-Chat"
                },
                "Eval_Statu": {
                    "VLMEvalKit": {
                        "Statu": 1,
                        "Datasets": "refcoco, refcoco+, mmiu, MMMU_DEV_VAL"
                    },
                    "VLMEvalKit_COT": {
                        "Statu": 0,
                        "Datasets": "MMMU_DEV_VAL, refbet"
                    },
                    "MIRB": 1,
                    "mmiu": 1
                }
            }
        };
        
        this.predefinedDatasets = [
            "refcoco", "refcoco+", "mmiu", "MMMU_DEV_VAL", "refbet",
            "coco", "imagenet", "vqa", "gqa", "vcr", "visual7w",
            "clevr", "nlvr", "textvqa", "stvqa", "ocr-vqa"
        ];
        
        this.isLoaded = true;
        console.log('Using default mock data');
    }

    // 获取模型配置数据
    getModelConfigs() {
        return this.mockData || {};
    }

    // 获取数据集列表
    getDatasets() {
        return this.predefinedDatasets || [];
    }

    // 获取数据集分类
    getDatasetCategories() {
        return this.datasetCategories || {};
    }

    // 获取评估指标信息
    getEvaluationMetrics() {
        return this.evaluationMetrics || {};
    }

    // 获取模型类型信息
    getModelTypes() {
        return this.modelTypes || {};
    }

    // 获取系统配置
    getSystemConfig() {
        return this.systemConfig || {};
    }

    // 获取元数据
    getMetadata() {
        return this.metadata || {};
    }

    // 获取评测状态数据
    getEvaluationStatus() {
        return this.evaluationStatus || {};
    }

    // 获取通用数据集列表
    getCommonDatasets() {
        return this.commonDatasets || {};
    }

    // 检查是否已加载
    isDataLoaded() {
        return this.isLoaded;
    }
}

// 创建全局数据加载器实例
const mockDataLoader = new MockDataLoader();

// 模拟API响应
const mockAPI = {
    // 模拟获取配置数据
    getConfig: function() {
        return new Promise(async (resolve) => {
            // 确保数据已加载
            if (!mockDataLoader.isDataLoaded()) {
                await mockDataLoader.loadMockData();
            }
            
            // 模拟网络延迟
            const delay = mockDataLoader.getSystemConfig().mock?.delay?.load || 500;
            setTimeout(() => {
                resolve({
                    success: true,
                    data: mockDataLoader.getModelConfigs(),
                    message: "模拟数据加载成功"
                });
            }, delay);
        });
    },

    // 模拟更新配置数据
    updateConfig: function(data) {
        return new Promise((resolve) => {
            const delay = mockDataLoader.getSystemConfig().mock?.delay?.update || 300;
            setTimeout(() => {
                resolve({
                    success: true,
                    message: "模拟数据更新成功",
                    updatedCount: Object.keys(data).length
                });
            }, delay);
        });
    },

    // 模拟健康检查
    healthCheck: function() {
        return new Promise((resolve) => {
            const delay = mockDataLoader.getSystemConfig().mock?.delay?.health || 100;
            setTimeout(() => {
                resolve({
                    success: true,
                    status: "healthy",
                    message: "模拟服务正常运行"
                });
            }, delay);
        });
    },

    // 获取数据集信息
    getDatasets: function() {
        return new Promise(async (resolve) => {
            if (!mockDataLoader.isDataLoaded()) {
                await mockDataLoader.loadMockData();
            }
            resolve({
                success: true,
                data: {
                    predefined: mockDataLoader.getDatasets(),
                    categories: mockDataLoader.getDatasetCategories(),
                    evaluationMetrics: mockDataLoader.getEvaluationMetrics()
                }
            });
        });
    },

    // 获取系统配置
    getSystemConfig: function() {
        return new Promise(async (resolve) => {
            if (!mockDataLoader.isDataLoaded()) {
                await mockDataLoader.loadMockData();
            }
            resolve({
                success: true,
                data: mockDataLoader.getSystemConfig()
            });
        });
    },

    // 获取评测状态数据
    getEvaluated: function() {
        return new Promise(async (resolve) => {
            if (!mockDataLoader.isDataLoaded()) {
                await mockDataLoader.loadMockData();
            }
            
            const delay = mockDataLoader.getSystemConfig().mock?.delay?.load || 500;
            setTimeout(() => {
                resolve({
                    status: 'success',
                    evaluation_status: mockDataLoader.getEvaluationStatus(),
                    common_datasets: mockDataLoader.getCommonDatasets(),
                    message: "评测状态数据加载成功"
                });
            }, delay);
        });
    }
};

// 数据管理类
class MockDataManager {
    constructor() {
        this.currentData = {};
        this.isUsingMock = false;
        this.lastUpdate = new Date();
        this.dataLoader = mockDataLoader;
    }

    // 初始化数据
    async initialize() {
        if (!this.dataLoader.isDataLoaded()) {
            await this.dataLoader.loadMockData();
        }
        this.currentData = JSON.parse(JSON.stringify(this.dataLoader.getModelConfigs()));
        return true;
    }

    // 获取当前数据
    getData() {
        return this.currentData;
    }

    // 更新数据
    updateData(newData) {
        this.currentData = newData;
        this.lastUpdate = new Date();
        return Promise.resolve({
            success: true,
            message: "模拟数据已更新",
            timestamp: this.lastUpdate
        });
    }

    // 添加新模型
    addModel(modelData) {
        const newId = (Math.max(...Object.keys(this.currentData).map(id => parseInt(id))) + 1).toString();
        this.currentData[newId] = modelData;
        return Promise.resolve({
            success: true,
            message: `新模型已添加 (ID: ${newId})`,
            newId: newId
        });
    }

    // 删除模型
    deleteModel(id) {
        if (this.currentData[id]) {
            delete this.currentData[id];
            return Promise.resolve({
                success: true,
                message: `模型 ${id} 已删除`
            });
        } else {
            return Promise.reject(new Error(`模型 ${id} 不存在`));
        }
    }

    // 获取数据集列表
    getDatasets() {
        return this.dataLoader.getDatasets();
    }

    // 获取数据集分类
    getDatasetCategories() {
        return this.dataLoader.getDatasetCategories();
    }

    // 获取评估指标信息
    getEvaluationMetrics() {
        return this.dataLoader.getEvaluationMetrics();
    }

    // 获取模型类型信息
    getModelTypes() {
        return this.dataLoader.getModelTypes();
    }

    // 获取系统配置
    getSystemConfig() {
        return this.dataLoader.getSystemConfig();
    }

    // 获取评测状态数据
    getEvaluationStatus() {
        return this.dataLoader.getEvaluationStatus();
    }

    // 获取通用数据集列表
    getCommonDatasets() {
        return this.dataLoader.getCommonDatasets();
    }

    // 获取统计信息
    getStats() {
        const totalModels = Object.keys(this.currentData).length;
        const completedEval = Object.values(this.currentData).filter(model => 
            model.Eval_Statu.VLMEvalKit.Statu === 1 || 
            model.Eval_Statu.VLMEvalKit_COT.Statu === 1
        ).length;
        
        return {
            totalModels: totalModels,
            completedEval: completedEval,
            pendingEval: totalModels - completedEval,
            lastUpdate: this.lastUpdate,
            metadata: this.dataLoader.getMetadata()
        };
    }

    // 重新加载数据
    async reloadData() {
        await this.dataLoader.loadMockData();
        this.currentData = JSON.parse(JSON.stringify(this.dataLoader.getModelConfigs()));
        this.lastUpdate = new Date();
        return true;
    }
}

// 创建全局实例
const mockDataManager = new MockDataManager();

// 初始化数据管理器
mockDataManager.initialize().then(() => {
    console.log('Mock data manager initialized successfully');
}).catch(error => {
    console.error('Failed to initialize mock data manager:', error);
});

// 导出到全局作用域
window.mockDataLoader = mockDataLoader;
window.mockAPI = mockAPI;
window.mockDataManager = mockDataManager;

// 为了向后兼容，保留旧的变量名
window.mockData = mockDataManager.getData();
window.predefinedDatasets = mockDataManager.getDatasets(); 