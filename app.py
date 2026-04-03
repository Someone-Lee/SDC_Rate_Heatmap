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
v_step = st.sidebar.slider("SDC Rate 步长 (仅限 <10V 区间)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
t_step = st.sidebar.slider("Time interval 步长", min_value=1.0, max_value=50.0, value=10.0, step=1.0)

# 3. 核心计算与绘图逻辑 (只有上传了文件才会执行)
if uploaded_file is not None:
    # 读取数据
    df = pd.read_excel(uploaded_file, usecols=[0, 1], names=['Time interval', 'SDC Rate'], header=0)
    df = df.dropna(subset=['Time interval', 'SDC Rate'])
    total_count = len(df)

    v_min, v_max = df['SDC Rate'].min(), df['SDC Rate'].max()
    t_min, t_max = df['Time interval'].min(), df['Time interval'].max()

    # 区间计算逻辑 (与之前相同)
    v_bins_list = []
    if v_min < 10:
        fine_bins = np.arange(v_min, 10, v_step).tolist()
        v_bins_list.extend(fine_bins)
        v_bins_list.append(10.0) 
        if v_max > 10:
            max_bound = np.ceil(v_max / 5.0) * 5.0
            v_bins_list.extend(np.arange(15.0, max_bound + 5.0, 5.0).tolist())
    else:
        v_bins_list.append(v_min)
        next_5 = np.ceil(v_min / 5.0) * 5.0
        if next_5 == v_min: next_5 += 5.0
        if v_max > v_min:
            max_bound = np.ceil(v_max / 5.0) * 5.0
            v_bins_list.extend(np.arange(next_5, max_bound + 5.0, 5.0).tolist())
            
    v_bins = np.unique(np.round(v_bins_list, 5)).tolist()
    t_bins = np.arange(t_min, t_max + t_step, t_step)

    # 安全限制，防止网页卡死
    if len(v_bins) > 80 or len(t_bins) > 80:
        st.error("⚠️ 步长太小导致生成的网格过多，请在左侧调大步长！")
    else:
        df['V_bin'] = pd.cut(df['SDC Rate'], bins=v_bins, include_lowest=True)
        df['T_bin'] = pd.cut(df['Time interval'], bins=t_bins, include_lowest=True)
        ct = pd.crosstab(df['V_bin'], df['T_bin'], margins=True, margins_name='Total', dropna=False)

        x_labels = [f"{i.left:.1f} ~ {i.right:.1f}" if str(i) != 'Total' else 'Total' for i in ct.columns]
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
                
                text_row.append("" if val == 0 else f"<b>{int(val)}</b><br><span style='font-size:10px'>({pct:.1f}%)</span>")
                hover_row.append(f"<b>SDC Rate:</b> {y_labels[i]}<br><b>Time:</b> {x_labels[j]}<br><b>Count:</b> {int(val)} ({pct:.1f}%)")
                
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
            xaxis_title="Time Interval (s)", yaxis_title="SDC Rate (V)",
            xaxis=dict(tickangle=-45), height=700, margin=dict(l=50, r=50, t=50, b=50)
        )

        # 在网页中渲染图表
        st.success(f"✅ 数据加载成功！共包含 {total_count} 条有效数据。")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("👈 请先在左侧上传 Excel 文件以查看分析图表。")