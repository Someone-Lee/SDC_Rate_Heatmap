import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. 网页全局设置
st.set_page_config(page_title="SDC Rate Analysis", layout="wide")
st.title("📊 SDC Rate vs Time Interval 密度分析")
st.markdown("请在左侧侧边栏上传您的数据，并调节步长。")

# 2. 侧边栏：文件上传与滑动条
st.sidebar.header("📁 1. 上传数据文件")
uploaded_file = st.sidebar.file_uploader("请上传 data.xlsx", type=["xlsx", "xls"])

st.sidebar.header("⚙️ 2. 调节步长")
v_step = st.sidebar.slider("SDC Rate 步长 (<10% 区间)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
t_step = st.sidebar.slider("Time interval 步长", min_value=1.0, max_value=50.0, value=10.0, step=1.0)

# 3. 核心计算与绘图逻辑
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, usecols=[0, 1], names=['Time interval', 'SDC Rate'], header=0)
    df = df.dropna(subset=['Time interval', 'SDC Rate'])
    total_count = len(df)

    v_min, v_max = df['SDC Rate'].min(), df['SDC Rate'].max()
    t_min, t_max = df['Time interval'].min(), df['Time interval'].max()

    # ==========================================
    # SDC Rate 区间生成算法 (%) - 保留固定步长逻辑
    # ==========================================
    v_bins_list = [v_min] 
    
    # 1. 小于 10% 的部分，受滑动条动态控制
    if v_min < 10.0:
        fine_bins = np.arange(v_min, 10.0, v_step).tolist()
        v_bins_list.extend(fine_bins)
        
    # 2. 10% 以上的部分，严格按照固定区间
    fixed_bounds = [10.0, 15.0, 20.0, 30.0, 40.0]
    
    if v_max > 40.0:
        curr_bound = 50.0
        while curr_bound <= v_max + 10.0:
            fixed_bounds.append(curr_bound)
            curr_bound += 10.0
            
    for b in fixed_bounds:
        if b > v_min:
            v_bins_list.append(b)
            
    v_bins = sorted(list(set(np.round(v_bins_list, 5))))

    # --- 时间区间（向下取整起点） ---
    t_start = np.floor(t_min)
    t_end = np.ceil(t_max)
    t_bins = np.arange(t_start, t_end + t_step, t_step)

    # 安全限制
    if len(v_bins) > 80 or len(t_bins) > 80:
        st.error("⚠️ 步长太小导致生成的网格过多，请在左侧调大步长！")
    else:
        df['V_bin'] = pd.cut(df['SDC Rate'], bins=v_bins, include_lowest=True)
        df['T_bin'] = pd.cut(df['Time interval'], bins=t_bins, include_lowest=True)
        ct = pd.crosstab(df['V_bin'], df['T_bin'], margins=True, margins_name='Total', dropna=False)

        x_labels = [f"{i.left:.0f} ~ {i.right:.0f}" if str(i) != 'Total' else 'Total' for i in ct.columns]
        y_labels = [f"{i.left:.2f} ~ {i.right:.2f}" if str(i) != 'Total' else 'Total' for i in ct.index]

        color_matrix = np.zeros(ct.shape)
        text_matrix = []
        hover_matrix = []
        rows, cols = ct.shape

        for i in range(rows):
            text_row = []
            hover_row = []
            for j in range(cols):
                val = ct.iloc[i, j]
                if pd.isna(val): val = 0
                pct = (val / total_count) * 100 if total_count > 0 else 0
                
                # --- 字体重叠优化 ---
                # 将数字和百分比放在同一行，并稍微调小字体大小
                cell_text = "" if val == 0 else f"<span style='font-size:14px'><b>{int(val)} ({pct:.1f}%)</b></span>"
                text_row.append(cell_text)
                
                # 悬浮提示文案修改
                hover_row.append(f"<b>SDC Rate (%):</b> {y_labels[i]}<br><b>Time:</b> {x_labels[j]}<br><b>Count:</b> {int(val)} ({pct:.1f}%)")
                
                color_matrix[i, j] = 0 if (i == rows - 1 or j == cols - 1) else val

            text_matrix.append(text_row)
            hover_matrix.append(hover_row)

        vmax = color_matrix.max() if color_matrix.max() > 0 else 1

        fig = go.Figure(data=go.Heatmap(
            z=color_matrix, x=x_labels, y=y_labels,
            text=text_matrix, texttemplate="%{text}",
            customdata=hover_matrix, hovertemplate="%{customdata}<extra></extra>",
            colorscale='Blues', zmin=0, zmax=vmax, showscale=True, xgap=2, ygap=2
        ))

        fig.update_layout(
            xaxis_title="<b>Time Interval (s)</b>", 
            yaxis_title="<b>SDC Rate (%)</b>",  # Y轴标题保持 % 描述
            xaxis=dict(tickangle=-45, tickfont=dict(size=13)), 
            yaxis=dict(tickfont=dict(size=13)),                
            height=750, 
            margin=dict(l=50, r=50, t=50, b=50)
        )

        st.success(f"✅ 数据加载成功！共包含 {total_count} 条有效数据。")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("👈 请先在左侧上传 Excel 文件以查看分析图表。")
